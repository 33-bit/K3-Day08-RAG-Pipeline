"""
Task 5 - Semantic Search & HyDE Search.
"""

from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_DIR / "chroma_db"

COLLECTION_NAME = "university_services_docs"
EMBEDDING_MODEL = "BAAI/bge-m3"


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def _distance_to_score(distance: float) -> float:
    score = 1.0 - float(distance)
    return round(max(0.0, min(1.0, score)), 4)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks by semantic similarity.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        sorted by score descending.
    """
    if not query or not query.strip():
        return []

    try:
        model = get_embedding_model()
        query_vector = model.encode(query).tolist()

        collection = get_collection()
        count = collection.count()
        if count == 0:
            return []

        n_results = min(top_k, count)

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append(
                {
                    "content": doc,
                    "score": _distance_to_score(dist),
                    "metadata": meta or {},
                }
            )

        output.sort(key=lambda x: x["score"], reverse=True)
        return output[:top_k]

    except Exception as e:
        print(f"Semantic search error: {e}")
        return []


def hyde_search(query: str, top_k: int = 10) -> list[dict]:
    """
    HyDE search: create a hypothetical document from the query,
    then use semantic search on that expanded text.
    """
    if not query or not query.strip():
        return []

    hypothetical_document = f"""
    This document answers the user question: {query}

    It contains relevant university service information such as tuition fees,
    payment methods, scholarships, student support, library services,
    accommodation, enrollment, course registration, academic policy,
    requirements, deadlines, and official student guidance.
    """

    return semantic_search(hypothetical_document, top_k=top_k)


if __name__ == "__main__":
    queries = [
        "What is the tuition fee payment policy?",
        "How can students apply for scholarships?",
        "What support services are available for students?",
    ]

    for q in queries:
        print("=" * 80)
        print("Query:", q)

        print("\nSemantic Search:")
        for r in semantic_search(q, top_k=3):
            print(f"[{r['score']:.4f}] {r['metadata']} | {r['content'][:150]}...")

        print("\nHyDE Search:")
        for r in hyde_search(q, top_k=3):
            print(f"[{r['score']:.4f}] {r['metadata']} | {r['content'][:150]}...")