"""Claude API로 Day별 단어+Quiz 데이터를 JSON 추출하는 스크립트.

사용법:
    python scripts/extract_words.py --day 1          # Day 01만 (샘플 테스트용)
    python scripts/extract_words.py --day 1 --day 5  # Day 01, 05만
    python scripts/extract_words.py --start 6 --end 10  # Day 06~10
    python scripts/extract_words.py                     # 전체 Day 01-30
"""

import argparse
import base64
import json
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CHUNKS_DIR = Path(__file__).resolve().parent.parent / "data" / "chunks"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "extracted"
LAYOUT_PDF = CHUNKS_DIR / "layout_guide.pdf"

WORD_EXTRACTION_PROMPT = """\
이 PDF는 토플 영단어 교재 '해커스 보카(초록이)'의 {day_label} 부분입니다.
함께 첨부된 레이아웃 설명 페이지를 참고하여 단어 데이터를 추출해주세요.

## 규칙

1. 한 단어가 여러 뜻을 가지면 meanings 배열에 각각 분리. 뜻 번호(1, 2, 3...)는 교재에 표기된 대로.
2. **기출동의어**(tested_synonyms)와 **중요동의어**(important_synonyms)를 구분:
   - 기출동의어: 녹색/강조색으로 표시된 동의어 (실제 시험에서 정답으로 출제됨)
   - 중요동의어: 일반 색상으로 표기된 동의어 (출제 가능성 높음)
   - 구분이 불확실하면 모두 tested_synonyms에 넣고 ocr_note에 "색상 구분 불확실" 기록
3. 한국어 뜻은 교재에 적힌 그대로 (의역하지 말 것)
4. 예문(example_en)은 교재 본문의 영어 예문. 표제어 부분도 그대로 포함.
5. 예문 해석(example_ko)은 해당 페이지 하단의 한국어 해석 블록에서 매칭하여 추출.
6. 파생어(derivatives)는 {{"pos": "n.", "word": "exploitation"}} 형태의 객체 배열.
7. 중요도(frequency)는 단어 옆의 별 개수 (1~3).
8. 최신출제 포인트(exam_tip)가 있는 단어만 해당 필드에 점선 박스 안의 전체 내용을 채움. 없으면 null.
9. OCR 오류가 의심되면 문맥상 올바른 단어로 교정하고, ocr_note에 "원본: XXX -> 교정: YYY" 형태로 기록.
10. Day 마지막 페이지의 **Quiz**(Choose the synonyms, 10문제)도 quiz 필드에 추출.
    - 각 문제의 단어, 보기(label + text), 정답 label을 모두 포함.
11. 출력은 순수 JSON만. 설명, 마크다운, 코드블럭 없이 JSON 객체만 출력.

## JSON 스키마

{{
  "day": "Day 01",
  "word_count": 57,
  "words": [
    {{
      "word_order": 1,
      "english": "exploit",
      "pronunciation": "[iksploit]",
      "frequency": 3,
      "derivatives": [{{"pos": "n.", "word": "exploitation"}}],
      "exam_tip": "exploit는 동사가 아닌 명사로도 많이 쓰인다. 명사로는 ...",
      "ocr_note": null,
      "meanings": [
        {{
          "order": 1,
          "part_of_speech": "v.",
          "korean": "(부당하게) 이용하다",
          "tested_synonyms": ["utilize", "use", "make use of", "take advantage of"],
          "important_synonyms": [],
          "example_en": "Human rights activists have led protests against companies that exploit child labor.",
          "example_ko": "인권 운동가들은 아동의 노동을 이용하는 회사들에 대항하는 시위를 이끌어 왔다."
        }}
      ]
    }}
  ],
  "quiz": {{
    "instruction": "Choose the synonyms.",
    "questions": [
      {{
        "number": 1,
        "word": "exploit",
        "choice_label": "c",
        "choice_text": "utilize, use, make use of",
        "answer_label": "c"
      }}
    ]
  }}
}}

PDF의 모든 단어를 빠짐없이 추출해주세요. 예상 단어 수: 56~57개.
"""


def load_pdf_as_base64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def parse_json_response(raw_text: str) -> dict | None:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_day(client: anthropic.Anthropic, day_num: int) -> dict | None:
    day_label = f"Day {day_num:02d}"
    chunk_path = CHUNKS_DIR / f"day_{day_num:02d}.pdf"

    if not chunk_path.exists():
        print(f"  [SKIP] {chunk_path.name} not found")
        return None

    size_mb = chunk_path.stat().st_size / 1024 / 1024
    print(f"  {day_label} 추출 중... ({size_mb:.1f}MB)")

    content: list[dict] = []

    if LAYOUT_PDF.exists():
        content.append({
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": load_pdf_as_base64(LAYOUT_PDF)},
            "cache_control": {"type": "ephemeral"},
        })

    content.append({
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": load_pdf_as_base64(chunk_path)},
    })

    content.append({"type": "text", "text": WORD_EXTRACTION_PROMPT.format(day_label=day_label)})

    collected_text = ""
    tokens_in = 0
    tokens_out = 0

    with client.messages.stream(
        model="claude-opus-4-20250514",
        max_tokens=16000,
        messages=[{"role": "user", "content": content}],
    ) as stream:
        for text in stream.text_stream:
            collected_text += text
        response = stream.get_final_message()
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens

    raw = collected_text

    data = parse_json_response(raw)

    if data is None:
        error_path = OUTPUT_DIR / f"day_{day_num:02d}_raw.txt"
        error_path.write_text(raw, encoding="utf-8")
        print(f"    [WARN] JSON 파싱 실패. 원본 저장: {error_path}")
        print(f"    tokens: {tokens_in}in + {tokens_out}out")
        return None

    word_count = len(data.get("words", []))
    quiz_count = len(data.get("quiz", {}).get("questions", []))
    print(f"    완료: {word_count}단어, Quiz {quiz_count}문제 (tokens: {tokens_in}in + {tokens_out}out)")

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude API로 Day별 단어 추출")
    parser.add_argument("--day", type=int, action="append", help="특정 Day만 (반복 가능)")
    parser.add_argument("--start", type=int, help="시작 Day")
    parser.add_argument("--end", type=int, help="끝 Day")
    args = parser.parse_args()

    if args.day:
        days = sorted(set(args.day))
    elif args.start is not None and args.end is not None:
        days = list(range(args.start, args.end + 1))
    elif args.start is not None or args.end is not None:
        parser.error("--start와 --end는 함께 사용해야 합니다")
    else:
        days = list(range(1, 31))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return

    client = anthropic.Anthropic()

    print(f"=== 단어 추출 시작: Day {days[0]:02d}~{days[-1]:02d} ({len(days)}개) ===\n")

    results = {}
    for i, day_num in enumerate(days):
        try:
            data = extract_day(client, day_num)
        except Exception as e:
            print(f"    [ERROR] {e}")
            data = None

        if data:
            out_path = OUTPUT_DIR / f"day_{day_num:02d}.json"
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            results[day_num] = data

        if i < len(days) - 1:
            time.sleep(2)

    print(f"\n=== 완료: {len(results)}/{len(days)} Day 추출 -> {OUTPUT_DIR} ===")
    total_words = sum(len(d.get("words", [])) for d in results.values())
    print(f"총 단어 수: {total_words}")


if __name__ == "__main__":
    main()
