"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ, tải nhanh)

Vector store options:
    - ChromaDB (local persistent)
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION
# =============================================================================

CHUNK_SIZE = 500        # Kích thước 500 ký tự phù hợp cho RAG retrieval
CHUNK_OVERLAP = 50      # Overlap 50 ký tự (10%) tránh đứt đoạn ngữ nghĩa
CHUNKING_METHOD = "recursive"

# Embedding Model: all-MiniLM-L6-v2 (nhẹ, 384 dim, nhanh)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"


# =============================================================================
# HELPER FUNCTIONS FOR OTHER TASKS
# =============================================================================

_MODEL_INSTANCE = None

def get_embedding_model():
    """Singleton getter cho SentenceTransformer model."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        from sentence_transformers import SentenceTransformer
        _MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL)
    return _MODEL_INSTANCE


def get_collection():
    """Getter cho ChromaDB Persistent Collection."""
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = md_file.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = relative_path.split("/", 1)[0].lower()
        if doc_type not in {"legal", "news"}:
            doc_type = "news" if "news" in relative_path.lower() else "legal"

        documents.append({
            "content": content,
            "metadata": {
                "source": relative_path,
                "file_name": md_file.name,
                "doc_type": doc_type,
                "type": doc_type,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        split_text = splitter.split_text
    except ImportError:
        def split_text(text):
            step = CHUNK_SIZE - CHUNK_OVERLAP
            return [text[start:start + CHUNK_SIZE] for start in range(0, len(text), step)]

    chunks = []
    for doc in documents:
        metadata = dict(doc.get("metadata", {}))
        source = metadata.get("source", "unknown")
        doc_type = metadata.get("doc_type", metadata.get("type", "unknown"))

        for index, chunk_text in enumerate(split_text(doc.get("content", ""))):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    **metadata,
                    "source": source,
                    "doc_type": doc_type,
                    "type": doc_type,
                    "chunk_index": index,
                },
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng embedding model.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    model = get_embedding_model()
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào ChromaDB theo batch 100 chunks.
    """
    collection = get_collection()

    batch_size = 100
    total_chunks = len(chunks)

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in batch]
        documents = [c["content"] for c in batch]
        embeddings = [c["embedding"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n+ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"+ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"+ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("+ Indexed to vector store successfully!")


if __name__ == "__main__":
    run_pipeline()
