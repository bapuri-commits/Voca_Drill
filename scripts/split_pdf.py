"""초록이 PDF를 Day/테스트 단위로 분할하는 스크립트."""

import sys
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter

SRC_PDF = Path(__file__).resolve().parent.parent / "docs" / "bookpdf" / "HACKERS VOCABULARY_David Cho_full.pdf"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "chunks"

# 페이지 맵
# 책에 인쇄된 페이지 번호와 PDF 물리적 페이지는 +4 오프셋이 있음.
# 예: 책 p.18 (Day 01 시작) = PDF 물리적 p.22
# 아래 값은 PDF 물리적 페이지 번호 (1-indexed).
OFFSET = 4  # PDF 물리적 페이지 = 책 인쇄 페이지 + OFFSET

# 책 인쇄 페이지 기준 맵 (분석 문서 기반)
_BOOK_PAGE_MAP: dict[str, tuple[int, int]] = {
    # 레이아웃 설명
    "layout_guide": (8, 9),
    # Day 01-05
    "day_01": (18, 27),
    "day_02": (28, 37),
    "day_03": (38, 47),
    "day_04": (48, 57),
    "day_05": (58, 67),
    # Day 06-10
    "day_06": (70, 79),
    "day_07": (80, 89),
    "day_08": (90, 99),
    "day_09": (100, 109),
    "day_10": (110, 119),
    # Day 11-15
    "day_11": (122, 131),
    "day_12": (132, 141),
    "day_13": (142, 151),
    "day_14": (152, 161),
    "day_15": (162, 171),
    # Day 16-20
    "day_16": (174, 183),
    "day_17": (184, 193),
    "day_18": (194, 203),
    "day_19": (204, 213),
    "day_20": (214, 223),
    # Day 21-25
    "day_21": (226, 235),
    "day_22": (236, 245),
    "day_23": (246, 255),
    "day_24": (256, 265),
    "day_25": (266, 275),
    # Day 26-30
    "day_26": (278, 287),
    "day_27": (288, 297),
    "day_28": (298, 307),
    "day_29": (308, 317),
    "day_30": (318, 327),
    # Review TEST (5Day마다)
    "review_test_01-05": (68, 69),
    "review_test_06-10": (120, 121),
    "review_test_11-15": (172, 173),
    "review_test_16-20": (224, 225),
    "review_test_21-25": (276, 277),
    "review_test_26-30": (328, 329),
    # Final TEST + Answer Key
    "final_tests": (330, 337),
}

# 오프셋 적용 → PDF 물리적 페이지 번호
PAGE_MAP: dict[str, tuple[int, int]] = {
    name: (start + OFFSET, end + OFFSET)
    for name, (start, end) in _BOOK_PAGE_MAP.items()
}


def split_pdf(src: Path = SRC_PDF, out_dir: Path = OUT_DIR) -> None:
    if not src.exists():
        print(f"[ERROR] PDF not found: {src}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(src))
    total_pages = len(reader.pages)
    print(f"원본 PDF: {total_pages}페이지")

    for name, (start, end) in PAGE_MAP.items():
        if end > total_pages:
            print(f"  [SKIP] {name}: p.{start}~{end} - 원본 범위 초과")
            continue

        writer = PdfWriter()
        for i in range(start - 1, end):  # 0-indexed
            writer.add_page(reader.pages[i])

        out_path = out_dir / f"{name}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)

        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  {name}.pdf - p.{start}~{end} ({end - start + 1}p, {size_mb:.1f}MB)")

    print(f"\n완료: {len(PAGE_MAP)}개 청크 → {out_dir}")


if __name__ == "__main__":
    split_pdf()
