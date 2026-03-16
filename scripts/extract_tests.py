"""Claude API로 Review TEST / Final TEST 데이터를 JSON 추출하는 스크립트.

사용법:
    python scripts/extract_tests.py              # Review TEST 6개 + Final TEST
    python scripts/extract_tests.py --review-only # Review TEST만
    python scripts/extract_tests.py --final-only  # Final TEST만
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

REVIEW_TESTS = [
    {"name": "review_test_01-05", "label": "Review TEST Day 1-5", "covers": ["Day 01", "Day 02", "Day 03", "Day 04", "Day 05"]},
    {"name": "review_test_06-10", "label": "Review TEST Day 6-10", "covers": ["Day 06", "Day 07", "Day 08", "Day 09", "Day 10"]},
    {"name": "review_test_11-15", "label": "Review TEST Day 11-15", "covers": ["Day 11", "Day 12", "Day 13", "Day 14", "Day 15"]},
    {"name": "review_test_16-20", "label": "Review TEST Day 16-20", "covers": ["Day 16", "Day 17", "Day 18", "Day 19", "Day 20"]},
    {"name": "review_test_21-25", "label": "Review TEST Day 21-25", "covers": ["Day 21", "Day 22", "Day 23", "Day 24", "Day 25"]},
    {"name": "review_test_26-30", "label": "Review TEST Day 26-30", "covers": ["Day 26", "Day 27", "Day 28", "Day 29", "Day 30"]},
]

REVIEW_TEST_PROMPT = """\
이 PDF는 토플 영단어 교재 '해커스 보카(초록이)'의 {label} 부분입니다.
테스트 문제를 아래 JSON 스키마에 맞춰 추출해주세요.

## 규칙

1. 모든 문제를 빠짐없이 추출
2. 문장 전체(question_text)와 밑줄/강조 단어(highlighted_word)를 구분
3. 보기 4개(A~D)를 정확히 포함
4. 정답(answer)은 보기 라벨(A/B/C/D)로 기재. 정답을 모르면 null.
5. 출력은 순수 JSON만. 설명, 마크다운, 코드블럭 없이.

## JSON 스키마

{{
  "test_name": "{label}",
  "covers": {covers_json},
  "question_count": 10,
  "questions": [
    {{
      "number": 1,
      "question_text": "The travelers replenished their supplies before the journey.",
      "highlighted_word": "replenished",
      "choices": {{
        "A": "increased",
        "B": "elevated",
        "C": "refilled",
        "D": "located"
      }},
      "answer": "C"
    }}
  ]
}}
"""

FINAL_TEST_PROMPT = """\
이 PDF는 토플 영단어 교재 '해커스 보카(초록이)'의 Final TEST 1~3과 Answer Key 부분입니다.
테스트 문제와 정답을 아래 JSON 스키마에 맞춰 추출해주세요.

## 규칙

1. Final TEST 1, 2, 3을 각각 별도 객체로 추출
2. 각 테스트의 모든 문제를 빠짐없이 추출
3. Answer Key 페이지에서 정답을 매칭하여 answer 필드에 기록
4. 문장 전체(question_text)와 밑줄/강조 단어(highlighted_word)를 구분
5. 보기 4개(A~D)를 정확히 포함
6. 출력은 순수 JSON 배열만.

## JSON 스키마

[
  {{
    "test_name": "Final TEST 1",
    "covers": ["Day 01", "Day 02", "...", "Day 30"],
    "question_count": 10,
    "questions": [
      {{
        "number": 1,
        "question_text": "...",
        "highlighted_word": "...",
        "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "answer": "A"
      }}
    ]
  }}
]
"""


def load_pdf_as_base64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def parse_json_response(raw_text: str) -> dict | list | None:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _stream_request(client: anthropic.Anthropic, content: list, max_tokens: int = 4096) -> tuple[str, int, int]:
    collected = ""
    with client.messages.stream(
        model="claude-opus-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    ) as stream:
        for text in stream.text_stream:
            collected += text
        resp = stream.get_final_message()
    return collected, resp.usage.input_tokens, resp.usage.output_tokens


def extract_review_test(client: anthropic.Anthropic, test_info: dict) -> dict | None:
    chunk_path = CHUNKS_DIR / f"{test_info['name']}.pdf"
    if not chunk_path.exists():
        print(f"  [SKIP] {chunk_path.name} not found")
        return None

    print(f"  {test_info['label']} 추출 중...")

    prompt = REVIEW_TEST_PROMPT.format(
        label=test_info["label"],
        covers_json=json.dumps(test_info["covers"]),
    )

    raw, ti, to = _stream_request(client, [
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": load_pdf_as_base64(chunk_path)}},
        {"type": "text", "text": prompt},
    ])

    data = parse_json_response(raw)
    if data is None:
        error_path = OUTPUT_DIR / f"{test_info['name']}_raw.txt"
        error_path.write_text(raw, encoding="utf-8")
        print(f"    [WARN] JSON 파싱 실패. 원본 저장: {error_path}")
        print(f"    tokens: {ti}in + {to}out")
        return None

    q_count = len(data.get("questions", []))
    print(f"    완료: {q_count}문제 (tokens: {ti}in + {to}out)")
    return data


def extract_final_tests(client: anthropic.Anthropic) -> list | None:
    chunk_path = CHUNKS_DIR / "final_tests.pdf"
    if not chunk_path.exists():
        print(f"  [SKIP] final_tests.pdf not found")
        return None

    print(f"  Final TEST 1~3 + Answer Key 추출 중...")

    raw, ti, to = _stream_request(client, [
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": load_pdf_as_base64(chunk_path)}},
        {"type": "text", "text": FINAL_TEST_PROMPT},
    ], max_tokens=8192)

    data = parse_json_response(raw)
    if data is None:
        error_path = OUTPUT_DIR / "final_tests_raw.txt"
        error_path.write_text(raw, encoding="utf-8")
        print(f"    [WARN] JSON 파싱 실패. 원본 저장: {error_path}")
        print(f"    tokens: {ti}in + {to}out")
        return None

    if isinstance(data, list):
        total_q = sum(len(t.get("questions", [])) for t in data)
        print(f"    완료: {len(data)}개 테스트, 총 {total_q}문제 (tokens: {ti}in + {to}out)")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude API로 테스트 데이터 추출")
    parser.add_argument("--review-only", action="store_true", help="Review TEST만")
    parser.add_argument("--final-only", action="store_true", help="Final TEST만")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return

    client = anthropic.Anthropic()

    do_review = not args.final_only
    do_final = not args.review_only

    print("=== 테스트 추출 시작 ===\n")

    if do_review:
        print("--- Review TEST ---\n")
        for test_info in REVIEW_TESTS:
            try:
                data = extract_review_test(client, test_info)
            except Exception as e:
                print(f"    [ERROR] {e}")
                data = None

            if data:
                out_path = OUTPUT_DIR / f"{test_info['name']}.json"
                out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(2)

    if do_final:
        print("\n--- Final TEST ---\n")
        try:
            data = extract_final_tests(client)
        except Exception as e:
            print(f"    [ERROR] {e}")
            data = None

        if data:
            out_path = OUTPUT_DIR / "final_tests.json"
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
