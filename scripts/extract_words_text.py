"""OCR PDF에서 텍스트를 추출한 뒤 Claude API로 단어+Quiz JSON을 생성하는 스크립트.

PDF를 이미지가 아닌 텍스트로 전달하여 토큰을 대폭 절약.
OCR PDF(텍스트 레이어 포함)가 필요.

사용법:
    python scripts/extract_words_text.py --day 9          # Day 09만
    python scripts/extract_words_text.py --start 9 --end 30  # Day 09~30
    python scripts/extract_words_text.py                     # 전체 Day 01-30
"""

import argparse
import json
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CHUNKS_DIR = Path(__file__).resolve().parent.parent / "data" / "chunks"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "extracted"

PROMPT_TEMPLATE = """\
아래는 토플 영단어 교재 '해커스 보카(초록이)'의 {day_label}에서 OCR로 추출한 텍스트입니다.

## 교재 레이아웃 참고
- 각 단어: 번호, 표제어, 품사, 동의어(기출=녹색강조/중요=일반), 한국어 뜻
- 발음기호: [ ] 안에 표기
- 파생어: 표제어 아래 품사+단어
- 예문: 영어 문장 (표제어 볼드), 페이지 하단에 한국어 해석
- 최신출제 포인트: 점선 박스 안 추가 정보 (선별적)
- Day 마지막에 Quiz (Choose the synonyms, 10문제)

## OCR 텍스트
{ocr_text}

## 규칙

1. 한 단어가 여러 뜻을 가지면 meanings 배열에 각각 분리
2. **기출동의어**(tested_synonyms)와 **중요동의어**(important_synonyms)를 구분:
   - OCR 텍스트에서 동의어 순서상 앞쪽(녹색 강조였던 것)이 기출, 뒤쪽이 중요
   - 구분이 불확실하면 모두 tested_synonyms에 넣고 ocr_note에 기록
3. 한국어 뜻은 교재에 적힌 그대로
4. 예문(example_en): 영어 예문, 예문 해석(example_ko): 한국어 해석
5. 파생어: {{"pos": "n.", "word": "exploitation"}} 형태
6. frequency: 별 개수 (1~3). OCR에서 별이 깨졌으면 단어 순서로 추정 (앞=3, 중간=2, 뒤=1)
7. 최신출제 포인트(exam_tip): 있는 단어만 채움
8. OCR 오류는 문맥상 교정하고 ocr_note에 기록
9. Quiz도 quiz 필드에 추출
10. 출력은 순수 JSON만

## JSON 스키마

{{
  "day": "{day_label}",
  "word_count": 56,
  "words": [
    {{
      "word_order": 1,
      "english": "exploit",
      "pronunciation": "[iksploit]",
      "frequency": 3,
      "derivatives": [{{"pos": "n.", "word": "exploitation"}}],
      "exam_tip": null,
      "ocr_note": null,
      "meanings": [
        {{
          "order": 1,
          "part_of_speech": "v.",
          "korean": "(부당하게) 이용하다",
          "tested_synonyms": ["utilize", "use", "make use of"],
          "important_synonyms": ["take advantage of"],
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
"""


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(f"--- Page {i+1} ---\n{text.strip()}")
    return "\n\n".join(pages)


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

    ocr_text = extract_text_from_pdf(chunk_path)
    if not ocr_text.strip():
        print(f"  [SKIP] {day_label}: no text extracted (not OCR PDF?)")
        return None

    text_chars = len(ocr_text)
    print(f"  {day_label} extracting... ({text_chars} chars)")

    prompt = PROMPT_TEMPLATE.format(day_label=day_label, ocr_text=ocr_text)

    collected = ""
    with client.messages.stream(
        model="claude-opus-4-20250514",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            collected += text
        response = stream.get_final_message()

    ti = response.usage.input_tokens
    to = response.usage.output_tokens
    print(f"    tokens: {ti}in + {to}out")

    data = parse_json_response(collected)
    if data is None:
        error_path = OUTPUT_DIR / f"day_{day_num:02d}_raw.txt"
        error_path.write_text(collected, encoding="utf-8")
        print(f"    [WARN] JSON parse failed. Raw saved: {error_path}")
        return None

    word_count = len(data.get("words", []))
    quiz_count = len(data.get("quiz", {}).get("questions", []))
    print(f"    done: {word_count} words, Quiz {quiz_count}q")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR text -> Claude -> JSON")
    parser.add_argument("--day", type=int, action="append", help="specific day(s)")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    if args.day:
        days = sorted(set(args.day))
    elif args.start is not None and args.end is not None:
        days = list(range(args.start, args.end + 1))
    elif args.start is not None or args.end is not None:
        parser.error("--start and --end must be used together")
    else:
        days = list(range(1, 31))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic()

    print(f"=== Text-based extraction: Day {days[0]:02d}~{days[-1]:02d} ({len(days)}) ===\n")

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

    print(f"\n=== Done: {len(results)}/{len(days)} Days ===")
    total_words = sum(len(d.get("words", [])) for d in results.values())
    print(f"Total words: {total_words}")


if __name__ == "__main__":
    main()
