"""
Diagnostic: shows the FULL ranked list of chunks against a query, so we
can see exactly where the expected correct chunk lands and how far off
it is — instead of only seeing whatever happens to be in the top 3.

Usage: python -m src.rag.diagnose
"""

import json
import numpy as np

from src.rag.embed import embed_passages, embed_query

QUERY = "What happens if I break my savings certificate early?"
QUERY_ARABIC = "ما هي غرامة كسر الشهادة قبل موعد الاستحقاق؟"  # same question, in Arabic — tests whether weak discrimination is specifically a cross-lingual issue
EXPECTED_SECTION = "كسر الشهادة"  # the chunk we believe SHOULD be the top match


def run_query(query: str, chunks: list[dict], chunk_vectors: np.ndarray):
    query_vector = np.array(embed_query(query))
    scores = chunk_vectors @ query_vector
    ranking = np.argsort(-scores)

    print(f"Query: {query!r}\n")
    print(f"Score range: {scores.min():.4f} to {scores.max():.4f}  (spread: {scores.max()-scores.min():.4f})")
    for rank, idx in enumerate(ranking[:10]):
        c = chunks[idx]
        section = c["metadata"]["section"].strip()
        marker = "  <-- EXPECTED MATCH" if section == EXPECTED_SECTION else ""
        print(f"  #{rank+1:2d}  score={scores[idx]:.4f}  [{section[:40]}]{marker}")
    expected_rank = [i for i, idx in enumerate(ranking) if chunks[idx]["metadata"]["section"].strip() == EXPECTED_SECTION]
    if expected_rank:
        print(f"  ... expected match rank: #{expected_rank[0]+1} of {len(chunks)}")
    print()


def main():
    with open("data/processed/chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Total chunks: {len(chunks)}")
    matches = [c for c in chunks if c["metadata"]["section"].strip() == EXPECTED_SECTION]
    print(f"Chunks with section == {EXPECTED_SECTION!r}: {len(matches)}")
    for m in matches:
        print("  ", repr(m["text"][:80]))
    print()

    embed_inputs = [f"{c['metadata']['section']}: {c['text']}" for c in chunks]
    chunk_vectors = np.array(embed_passages(embed_inputs))

    print("=" * 60)
    print("ENGLISH QUERY")
    print("=" * 60)
    run_query(QUERY, chunks, chunk_vectors)

    print("=" * 60)
    print("ARABIC QUERY (same question)")
    print("=" * 60)
    run_query(QUERY_ARABIC, chunks, chunk_vectors)


if __name__ == "__main__":
    main()
