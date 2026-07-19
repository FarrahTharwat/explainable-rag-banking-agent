"""
PDF text extraction for CBE circulars.

Earlier version relied on PyMuPDF's default get_text(), which for this
document's Arabic encoding sometimes splits a single word into multiple
"line" objects even though they occupy the exact same visual line on the
page (a glyph-run artifact). That broke text-matching downstream.

This version reconstructs lines itself from raw word/span positions:
spans are grouped into visual lines by y-coordinate proximity (not by
PyMuPDF's own line grouping, which proved unreliable here), then ordered
right-to-left by x-coordinate within each line — correct for Arabic.
This also gives us font name + bold flag per line, which is what the
chunking step uses to detect section headings instead of matching
specific words.
"""

import fitz  # pymupdf

Y_TOLERANCE = 3  # points; spans within this y-distance are treated as the same visual line


def extract_structured_lines(pdf_path: str) -> list[dict]:
    """
    Extract text from a PDF as a list of visually-reconstructed lines.

    Returns: [{"page": 1, "text": "...", "is_bold": True, "font": "...", "y0": 54.2}, ...]
    Lines are returned in reading order: page ascending, then top-to-bottom.
    """
    doc = fitz.open(pdf_path)
    all_lines = []

    for page_num, page in enumerate(doc):
        spans = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for s in line["spans"]:
                    if s["text"].strip():
                        spans.append(s)

        # Group spans into real visual lines by y-position, ignoring
        # PyMuPDF's own (unreliable, for this doc) line boundaries.
        spans.sort(key=lambda s: s["bbox"][1])
        visual_lines = []
        for s in spans:
            y0 = s["bbox"][1]
            placed = False
            for vl in visual_lines:
                if abs(vl["y0"] - y0) < Y_TOLERANCE:
                    vl["spans"].append(s)
                    placed = True
                    break
            if not placed:
                visual_lines.append({"y0": y0, "spans": [s]})

        for vl in visual_lines:
            ordered = sorted(vl["spans"], key=lambda s: -s["bbox"][0])  # right-to-left
            text = "".join(s["text"] for s in ordered).strip()
            if not text:
                continue

            bold_count = sum(1 for s in ordered if (s["flags"] & 16) or "Bold" in s["font"])
            is_bold = bold_count == len(ordered)
            # majority font on the line (usually all spans share one font)
            font = max(set(s["font"] for s in ordered), key=lambda f: sum(1 for s in ordered if s["font"] == f))

            all_lines.append({
                "page": page_num + 1,
                "text": text,
                "is_bold": is_bold,
                "font": font,
                "y0": vl["y0"],
            })

    doc.close()
    return all_lines


if __name__ == "__main__":
    import sys
    import json

    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python -m src.ingestion.extract <path_to_pdf>")
        sys.exit(1)

    lines = extract_structured_lines(path)
    print(f"Extracted {len(lines)} lines total\n")
    print(json.dumps(lines[:5], ensure_ascii=False, indent=2))
