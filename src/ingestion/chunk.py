"""
Chunking logic for CBE circular text.

Chunks should respect natural document structure (numbered clauses,
template sections) rather than blind fixed-size splitting where possible.
Each chunk should carry metadata: source document, date, category.
"""


def chunk_document(text: str, source_metadata: dict) -> list[dict]:
    """Split cleaned text into chunks with attached metadata."""
    raise NotImplementedError
