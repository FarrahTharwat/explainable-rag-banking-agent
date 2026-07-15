"""
Vector store setup and retrieval (Chroma).
Supports metadata filtering (e.g. by category or document date).
"""


def build_index(chunks: list[dict]):
    raise NotImplementedError


def retrieve(query: str, k: int = 5):
    raise NotImplementedError
