"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    class BM25Okapi:
        """Pure-Python BM25Okapi fallback when rank-bm25 is not installed."""
        def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
            self.k1 = k1
            self.b = b
            self.corpus_size = len(corpus)
            self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 0
            self.doc_freqs = []
            self.doc_len = []
            self.nd = {}
            for doc in corpus:
                self.doc_len.append(len(doc))
                freq = {}
                for word in doc:
                    freq[word] = freq.get(word, 0) + 1
                self.doc_freqs.append(freq)
                for word in freq:
                    self.nd[word] = self.nd.get(word, 0) + 1
            self.idf = {}
            for word, freq in self.nd.items():
                self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

        def get_scores(self, query: list[str]) -> np.ndarray:
            scores = np.zeros(self.corpus_size)
            for word in query:
                if word not in self.idf:
                    continue
                idf = self.idf[word]
                for i, doc_freq in enumerate(self.doc_freqs):
                    if word in doc_freq:
                        freq = doc_freq[word]
                        numerator = freq * (self.k1 + 1)
                        denominator = freq + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avgdl or 1))
                        scores[i] += idf * (numerator / denominator)
            return scores

CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}

BM25_K1 = 1.5
BM25_B = 0.75


def load_corpus() -> list[dict]:
    """Auto-load corpus from standardized docs if CORPUS is empty."""
    global CORPUS
    if not CORPUS:
        try:
            from src.task4_chunking_indexing import load_documents, chunk_documents
            raw_docs = load_documents()
            if raw_docs:
                CORPUS = chunk_documents(raw_docs)
        except Exception:
            pass
    return CORPUS



def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản, nhất quán cho cả corpus và query."""
    cleaned = text.lower().replace("-", " ").replace("_", " ").replace(".", " ")
    return cleaned.split()



def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not CORPUS:
        load_corpus()

    if not CORPUS or top_k <= 0:
        return []

    bm25 = build_bm25_index(CORPUS)
    scores = bm25.get_scores(_tokenize(query))
    return _format_ranked_results(scores, top_k)


def tfidf_search(query: str, top_k: int = 10) -> list[dict]:
    """Tìm kiếm từ khóa bằng TF-IDF và cosine similarity.

    Trả về cùng định dạng với :func:`lexical_search` để hai phương pháp có
    thể được so sánh trực tiếp trên cùng corpus và truy vấn.
    """
    if not CORPUS:
        load_corpus()

    if not CORPUS or top_k <= 0:
        return []

    vectorizer = TfidfVectorizer(lowercase=True)
    document_matrix = vectorizer.fit_transform(
        [doc["content"] for doc in CORPUS]
    )
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, document_matrix).ravel()
    return _format_ranked_results(scores, top_k)



def _format_ranked_results(scores: np.ndarray, top_k: int) -> list[dict]:
    """Chuyển điểm sparse retrieval thành format kết quả chung."""
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for index in top_indices:
        score = float(scores[index])
        if score <= 0:
            continue
        document = CORPUS[index]
        results.append(
            {
                "content": document["content"],
                "score": score,
                "metadata": document["metadata"],
            }
        )
    return results


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Test
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

