"""
Chunking logic for CBE circular text.

Section boundaries are detected structurally, not by matching specific
words: a line starts a new section if it's bold AND uses a "content" font
(TimesNewRoman/Calibri family in this document) rather than the "cover
letter" font (Arial family). This was determined by inspecting the real
font usage in the source PDF — see docs/architecture.md for the full
investigation. Content-font bold lines include both top-level template
titles ("Basic Data Form for Savings Account") and finer sub-topic labels
("Fees", "Return Calculation", "Early Break Penalty") — by design, this
produces fine-grained, topically tight chunks rather than a few large ones,
which is generally better for retrieval precision.

Everything before the first detected heading is treated as the document's
cover letter / preamble and kept as a single section.

NOTE: HEADING_FONT_EXCLUDE_SUBSTR is tuned against this document's fonts.
When adding new circulars, check their font usage (see extract.py's
__main__ block or docs/architecture.md) before assuming this transfers —
different circulars may use different font families for non-heading text.
"""

# Bold lines using a font containing this substring are treated as regular
# text (e.g. cover-letter formatting), not section headings.
HEADING_FONT_EXCLUDE_SUBSTR = "Arial"

# A bold, correct-font line still isn't necessarily a real heading — table
# artifacts (e.g. a single bold cell like "تراكم") and signature-line
# placeholders (e.g. "..........") can also come back bold. Require the
# heading candidate to have a minimum number of actual letters (not just
# punctuation/digits/dots) before treating it as a real section title.
MIN_HEADING_LETTERS = 4

CHUNK_SIZE = 1200       # characters per chunk (rough proxy for tokens) — safety net for unusually long sections
CHUNK_OVERLAP = 200


def is_heading(line: dict) -> bool:
    """
    A line counts as a section heading if it's bold, not in the excluded
    (body-text) font family, and contains enough actual letters to be a
    real title rather than table/formatting noise.
    """
    if not line["is_bold"] or HEADING_FONT_EXCLUDE_SUBSTR in line["font"]:
        return False
    letter_count = sum(1 for ch in line["text"] if ch.isalpha())
    return letter_count >= MIN_HEADING_LETTERS


def split_into_sections(lines: list[dict]) -> list[dict]:
    """
    Group structured lines (see extract.extract_structured_lines) into
    sections, splitting wherever is_heading() is True.
    """
    sections = []
    current_title = "cover_letter"
    current_lines = []

    for line in lines:
        if is_heading(line):
            if current_lines:
                sections.append({"title": current_title, "text": "\n".join(current_lines)})
            current_title = line["text"]
            current_lines = []
        else:
            current_lines.append(line["text"])

    if current_lines:
        sections.append({"title": current_title, "text": "\n".join(current_lines)})

    return sections


def split_into_windows(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Fixed-size sliding window split, used only if a section is unusually long."""
    if len(text) <= size:
        return [text]
    windows = []
    start = 0
    while start < len(text):
        windows.append(text[start:start + size])
        start += size - overlap
    return windows


def chunk_document(lines: list[dict], source_metadata: dict) -> list[dict]:
    """
    Full pipeline: group structured lines into sections, then split any
    unusually long section into embedding-sized windows.

    source_metadata example:
        {"source_file": "circular_2024_12_24.pdf", "date": "2024-12-24",
         "category": "Consumer Protection"}
    """
    sections = split_into_sections(lines)

    chunks = []
    for section in sections:
        windows = split_into_windows(section["text"])
        for idx, window_text in enumerate(windows):
            chunks.append({
                "text": window_text,
                "metadata": {
                    **source_metadata,
                    "section": section["title"],
                    "chunk_index": idx,
                },
            })

    return chunks


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from src.ingestion.extract import extract_structured_lines

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not pdf_path:
        print("Usage: python -m src.ingestion.chunk <path_to_pdf>")
        sys.exit(1)

    lines = extract_structured_lines(pdf_path)
    chunks = chunk_document(lines, {
        "source_file": pdf_path.split("/")[-1],
        "date": "2024-12-24",
        "category": "Consumer Protection",
    })

    print(f"Produced {len(chunks)} chunks\n")
    for c in chunks:
        preview = c["text"][:50].replace("\n", " ")
        print(f"[{c['metadata']['section'][:45]}] ({len(c['text'])} chars): {preview}...")
