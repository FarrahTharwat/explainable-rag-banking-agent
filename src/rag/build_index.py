"""
Entry point: reads data/processed/chunks.json (produced by
src.ingestion.build_corpus), embeds every chunk, and builds the
persistent Chroma vector store at data/processed/chroma_store.

Usage: python -m src.rag.build_index
"""

import json
from pathlib import Path

from src.rag.vector_store import build_index

CHUNKS_PATH = Path("data/processed/chunks.json")


def main():
    if not CHUNKS_PATH.exists():
        print(f"{CHUNKS_PATH} not found — run `python -m src.ingestion.build_corpus` first.")
        return

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    build_index(chunks)


if __name__ == "__main__":
    main()
