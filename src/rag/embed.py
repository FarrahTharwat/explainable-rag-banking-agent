"""
Embedding model wrapper.

Uses a multilingual sentence-embedding model so a question in English can
retrieve an Arabic chunk (and vice versa) — the model maps both into the
same vector space based on meaning, not surface language.

Model: intfloat/multilingual-e5-base. Note this model expects a "query: "
or "passage: " prefix on input text (part of how it was trained) —
skipping the prefix works but gives noticeably worse retrieval quality,
so don't drop it even though it looks redundant.
"""

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()  # reads .env into the environment so EMBEDDING_MODEL etc. actually take effect

_model = None  # lazy-loaded singleton so we don't reload the model on every call

# Default model — override by setting EMBEDDING_MODEL in your .env file.
# Using the large variant by default: testing on this project's real corpus
# showed base struggled with cross-lingual (English query -> Arabic chunk)
# retrieval — correct chunk ranked #13 of 55 — while large ranked it #3 of 55
# on the same query (see docs/architecture.md for the full comparison).
# The tradeoff is a heavier download (~2.2GB vs ~450MB) — worth it here since
# cross-lingual retrieval is the whole point of this project.
DEFAULT_MODEL = "intfloat/multilingual-e5-large"


def get_embedding_model(model_name: str = None) -> SentenceTransformer:
    global _model
    if _model is None:
        resolved_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
        _model = SentenceTransformer(resolved_name)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed document chunks for storage. Use this for corpus text, not queries."""
    model = get_embedding_model()
    prefixed = [f"passage: {t}" for t in texts]
    return model.encode(prefixed, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """Embed a user question for retrieval. Use this for queries, not corpus text."""
    model = get_embedding_model()
    return model.encode(f"query: {text}", normalize_embeddings=True).tolist()


if __name__ == "__main__":
    # Quick sanity check: an English query should score highest against
    # its true Arabic match, not against an unrelated Arabic chunk.
    sample_chunks = [
        "رسوم فتح الحساب: يتم تحصيل رسوم قدرها 50 جنيه عند فتح حساب التوفير",  # account opening fees
        "غرامة كسر الشهادة قبل تاريخ الاستحقاق تعادل نسبة من قيمة الشهادة",       # early break penalty
    ]
    query = "What is the penalty for breaking a certificate early?"

    chunk_vectors = embed_passages(sample_chunks)
    query_vector = embed_query(query)

    import numpy as np
    scores = [float(np.dot(query_vector, cv)) for cv in chunk_vectors]
    print("Similarity scores (higher = more relevant):")
    for chunk, score in zip(sample_chunks, scores):
        print(f"  {score:.4f} — {chunk[:50]}...")
    print(f"\nExpected: chunk 2 (early break penalty) should score highest.")
