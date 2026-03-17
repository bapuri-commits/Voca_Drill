"""VPS용 — 전체 PDF를 Day별 + Test별로 분할."""

import sys
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter

PDF_DIR = Path("/app/data/pdf")
SRC_PDF = PDF_DIR / "HACKERS VOCABULARY_David Cho.pdf"
DAY_DIR = PDF_DIR / "day"
TEST_DIR = PDF_DIR / "test"

OFFSET = 4

DAY_MAP: dict[str, tuple[int, int]] = {
    "Day 01": (18, 27), "Day 02": (28, 37), "Day 03": (38, 47),
    "Day 04": (48, 57), "Day 05": (58, 67),
    "Day 06": (70, 79), "Day 07": (80, 89), "Day 08": (90, 99),
    "Day 09": (100, 109), "Day 10": (110, 119),
    "Day 11": (122, 131), "Day 12": (132, 141), "Day 13": (142, 151),
    "Day 14": (152, 161), "Day 15": (162, 171),
    "Day 16": (174, 183), "Day 17": (184, 193), "Day 18": (194, 203),
    "Day 19": (204, 213), "Day 20": (214, 223),
    "Day 21": (226, 235), "Day 22": (236, 245), "Day 23": (246, 255),
    "Day 24": (256, 265), "Day 25": (266, 275),
    "Day 26": (278, 287), "Day 27": (288, 297), "Day 28": (298, 307),
    "Day 29": (308, 317), "Day 30": (318, 327),
}

TEST_MAP: dict[str, tuple[int, int]] = {
    "Review TEST 01-05": (68, 69),
    "Review TEST 06-10": (120, 121),
    "Review TEST 11-15": (172, 173),
    "Review TEST 16-20": (224, 225),
    "Review TEST 21-25": (276, 277),
    "Review TEST 26-30": (328, 329),
    "Final TEST": (330, 337),
}


def split(reader, page_map, out_dir, total):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (book_start, book_end) in page_map.items():
        start = book_start + OFFSET
        end = book_end + OFFSET
        if end > total:
            print(f"  SKIP {name}: out of range")
            continue
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        out_path = out_dir / f"{name}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  {name}.pdf ({end - start + 1}p, {size_mb:.1f}MB)")


def main():
    if not SRC_PDF.exists():
        print(f"ERROR: {SRC_PDF} not found")
        sys.exit(1)

    reader = PdfReader(str(SRC_PDF))
    total = len(reader.pages)
    print(f"Source: {total} pages")

    print(f"\n[Day]")
    split(reader, DAY_MAP, DAY_DIR, total)

    print(f"\n[Test]")
    split(reader, TEST_MAP, TEST_DIR, total)

    print(f"\nDone: {len(DAY_MAP)} days + {len(TEST_MAP)} tests")


if __name__ == "__main__":
    main()
