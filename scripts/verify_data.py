"""추출된 JSON 데이터를 검증하는 스크립트.

사용법:
    python scripts/verify_data.py                # data/extracted/ 전체 검증
    python scripts/verify_data.py --day 1        # Day 01만 검증
"""

import argparse
import json
from pathlib import Path

EXTRACTED_DIR = Path(__file__).resolve().parent.parent / "data" / "extracted"


def verify_day(path: Path) -> dict:
    """Day JSON 파일 검증. 오류 목록을 반환."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"file": path.name, "errors": [f"JSON 파싱 실패: {e}"], "warnings": []}

    day = data.get("day", "?")

    words = data.get("words", [])
    if not words:
        errors.append("words 배열이 비어있음")

    word_count = len(words)
    if word_count < 50 or word_count > 60:
        warnings.append(f"단어 수 {word_count}개 - 예상 범위(50~60) 밖")

    stated_count = data.get("word_count")
    if stated_count is not None and stated_count != word_count:
        errors.append(f"word_count({stated_count}) != 실제 단어 수({word_count})")

    seen_english: set[str] = set()
    ocr_notes: list[str] = []

    for i, w in enumerate(words):
        idx = f"#{w.get('word_order', i+1)}"

        if not w.get("english"):
            errors.append(f"{idx}: english 필드 없음")
            continue

        english = w["english"]

        if english in seen_english:
            warnings.append(f"{idx} {english}: 중복 단어")
        seen_english.add(english)

        freq = w.get("frequency", 0)
        if freq not in (1, 2, 3):
            warnings.append(f"{idx} {english}: frequency={freq} (1~3 범위 밖)")

        if w.get("ocr_note"):
            ocr_notes.append(f"{idx} {english}: {w['ocr_note']}")

        meanings = w.get("meanings", [])
        if not meanings:
            errors.append(f"{idx} {english}: meanings 배열이 비어있음")

        for j, m in enumerate(meanings):
            m_idx = f"{idx}.뜻{m.get('order', j+1)}"

            if not m.get("korean"):
                errors.append(f"{m_idx} {english}: korean 필드 없음")

            tested = m.get("tested_synonyms", [])
            important = m.get("important_synonyms", [])
            if not tested and not important:
                warnings.append(f"{m_idx} {english}: 동의어가 하나도 없음")
            elif not tested:
                warnings.append(f"{m_idx} {english}: tested_synonyms가 비어있음 (important만 있음)")

    quiz = data.get("quiz")
    if not quiz:
        warnings.append("quiz 필드 없음")
    else:
        questions = quiz.get("questions", [])
        if len(questions) != 10:
            warnings.append(f"quiz 문제 수: {len(questions)}개 (예상: 10)")

    return {
        "file": path.name,
        "day": day,
        "word_count": word_count,
        "errors": errors,
        "warnings": warnings,
        "ocr_notes": ocr_notes,
    }


def verify_test(path: Path) -> dict:
    """Review/Final TEST JSON 파일 검증."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"file": path.name, "errors": [f"JSON 파싱 실패: {e}"], "warnings": []}

    if isinstance(data, list):
        for test in data:
            _verify_single_test(test, errors, warnings)
    else:
        _verify_single_test(data, errors, warnings)

    return {"file": path.name, "errors": errors, "warnings": warnings}


def _verify_single_test(test: dict, errors: list, warnings: list) -> None:
    name = test.get("test_name", "?")
    questions = test.get("questions", [])

    if not questions:
        errors.append(f"{name}: questions 배열이 비어있음")
        return

    for q in questions:
        num = q.get("number", "?")
        if not q.get("highlighted_word"):
            warnings.append(f"{name} Q{num}: highlighted_word 없음")
        if not q.get("choices"):
            errors.append(f"{name} Q{num}: choices 없음")
        if q.get("answer") is None:
            warnings.append(f"{name} Q{num}: answer가 null")


def main() -> None:
    parser = argparse.ArgumentParser(description="추출 데이터 검증")
    parser.add_argument("--day", type=int, help="특정 Day만 검증")
    args = parser.parse_args()

    if not EXTRACTED_DIR.exists():
        print(f"[ERROR] 추출 디렉토리 없음: {EXTRACTED_DIR}")
        return

    if args.day:
        files = [EXTRACTED_DIR / f"day_{args.day:02d}.json"]
    else:
        files = sorted(EXTRACTED_DIR.glob("*.json"))

    if not files:
        print("검증할 파일이 없습니다.")
        return

    total_errors = 0
    total_warnings = 0
    total_words = 0

    print("=" * 60)
    print("데이터 검증 결과")
    print("=" * 60)

    for f in files:
        if not f.exists():
            print(f"\n[SKIP] {f.name} - 파일 없음")
            continue

        if f.name.startswith("day_"):
            result = verify_day(f)
            total_words += result.get("word_count", 0)
        elif f.name.startswith("review_test") or f.name.startswith("final_test"):
            result = verify_test(f)
        else:
            continue

        errors = result.get("errors", [])
        warnings = result.get("warnings", [])
        ocr_notes = result.get("ocr_notes", [])

        total_errors += len(errors)
        total_warnings += len(warnings)

        status = "OK" if not errors else "ERROR"
        extra = f" ({result.get('word_count', '?')}단어)" if "word_count" in result else ""
        print(f"\n[{status}] {result['file']}{extra}")

        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        for n in ocr_notes:
            print(f"  OCR:   {n}")

    print("\n" + "=" * 60)
    print(f"총 단어: {total_words}개")
    print(f"오류: {total_errors}개, 경고: {total_warnings}개")
    if total_errors == 0:
        print("검증 통과")
    else:
        print("검증 실패 — 오류 수정 필요")


if __name__ == "__main__":
    main()
