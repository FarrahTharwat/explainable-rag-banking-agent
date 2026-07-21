"""
Vector store setup and retrieval using Chroma.

Chroma was picked over raw FAISS for this project because it natively
stores metadata (source file, date, category, section) alongside each
vector and supports filtering on it at query time — e.g. "only search
within Consumer Protection circulars" — without extra bookkeeping.
"""

import chromadb
from src.rag.embed import embed_passages, embed_query

DEFAULT_COLLECTION_NAME = "cbe_circulars"


def get_client(persist_path: str = "data/processed/chroma_store"):
    return chromadb.PersistentClient(path=persist_path)


def build_index(chunks: list[dict], persist_path: str = "data/processed/chroma_store",
                 collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Embed and store chunks (as produced by src.ingestion.chunk.chunk_document).
    Safe to re-run — recreates the collection from scratch each time.
    """
    client = get_client(persist_path)

    # Drop and recreate so re-running this doesn't duplicate entries
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    texts = [c["text"] for c in chunks]

    # Embed with the section title prepended — gives the model explicit
    # topic signal a bare chunk body sometimes lacks (e.g. a chunk that
    # says "the table below shows penalties..." without ever using the
    # word "certificate" itself). We still STORE and DISPLAY the original
    # untouched text — only the embedding input gets the title prefix.
    embed_inputs = [f"{c['metadata']['section']}: {c['text']}" for c in chunks]
    vectors = embed_passages(embed_inputs)

    # Chroma metadata values must be str/int/float/bool — None isn't allowed,
    # so swap any missing values (e.g. an unset date) for an empty string.
    metadatas = []
    for c in chunks:
        clean_meta = {k: (v if v is not None else "") for k, v in c["metadata"].items()}
        metadatas.append(clean_meta)

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Indexed {len(chunks)} chunks into collection '{collection_name}' at {persist_path}")
    return collection


def retrieve(query: str, k: int = 5, persist_path: str = "data/processed/chroma_store",
             collection_name: str = DEFAULT_COLLECTION_NAME, category_filter: str = None):
    """
    Retrieve the k most relevant chunks for a query.
    Pass category_filter (e.g. "Consumer Protection") to restrict the search.
    """
    client = get_client(persist_path)
    collection = client.get_collection(collection_name)

    query_vector = embed_query(query)

    where = {"category": category_filter} if category_filter else None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where,
    )

    hits = []
    for doc, meta, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        hits.append({"text": doc, "metadata": meta, "distance": distance})
    return hits


if __name__ == "__main__":
    import sys
    import json

    sys.path.insert(0, ".")

    with open("data/processed/chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)

    build_index(chunks)

    print("\n--- Test query ---")
    results = retrieve("What happens if I break my savings certificate early?", k=3)
    for r in results:
        print(f"\n[{r['metadata']['section'][:40]}] (distance: {r['distance']:.4f})")
        print(r["text"][:150].replace("\n", " "))
