"""
Entry point: reads every PDF in data/raw/, extracts + chunks it, and
writes the combined chunk list to data/processed/chunks.json.

Per-file metadata (date, category) is pulled from data/raw/manifest.json
if present — see manifest.json for the expected format. Files not listed
there still get processed, just with "category": "Unknown" and no date,
so nothing silently gets skipped; you'll just want to fill in the
manifest for anything that matters for retrieval/eval later.

Usage: python -m src.ingestion.build_corpus
"""

import json
from pathlib import Path

from src.ingestion.extract import extract_structured_lines
from src.ingestion.chunk import chunk_document

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MANIFEST_PATH = RAW_DIR / "manifest.json"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_corpus():
    manifest = load_manifest()
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {RAW_DIR}/ — add some circulars first.")
        return

    all_chunks = []
    for pdf_path in pdf_files:
        filename = pdf_path.name
        meta = manifest.get(filename, {})
        if not meta:
            print(f"⚠️  No manifest entry for {filename} — using defaults. "
                  f"Add one to {MANIFEST_PATH} for accurate date/category metadata.")

        source_metadata = {
            "source_file": filename,
            "date": meta.get("date"),
            "category": meta.get("category", "Unknown"),
        }

        lines = extract_structured_lines(str(pdf_path))
        chunks = chunk_document(lines, source_metadata)
        all_chunks.extend(chunks)
        print(f"✓ {filename}: {len(chunks)} chunks")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(all_chunks)} total chunks to {out_path}")


if __name__ == "__main__":
    build_corpus()
