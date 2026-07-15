"""
Embedding model wrapper. Uses a multilingual embedding model so English
queries can retrieve Arabic source chunks and vice versa.
"""


def get_embedding_model():
    raise NotImplementedError
