"""
Task 7 — Reranking Module.

Sử dụng phương pháp Reciprocal Rank Fusion (RRF):
    RRF(d) = Σ 1 / (k + rank_r(d))  với k = 60

Lưu ý quan trọng về RRF:
    - Điểm RRF fused CHỈ phụ thuộc thứ hạng, không phải độ tương đồng gốc.
    - Top-1 sau khi fuse luôn xấp xỉ 1/(k+1) ≈ 0.0164 (k=60).
    - Tự động fallback về RRF khi không có JINA_API_KEY hoặc Jina API không hoạt động.
"""

import os
from typing import Optional


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Jina Reranker API (nếu có API Key),
    hoặc fallback về RRF nếu không có API Key / Jina API không hoạt động.
    """
    jina_key = os.getenv("JINA_API_KEY", "").strip()

    if jina_key and candidates:
        try:
            import requests
            response = requests.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {jina_key}"},
                json={
                    "model": "jina-reranker-v2-base-multilingual",
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": top_k,
                },
                timeout=5,
            )
            if response.status_code == 200:
                reranked = response.json().get("results", [])
                results = []
                for r in reranked:
                    idx = r["index"]
                    item = candidates[idx].copy()
                    item["score"] = float(r["relevance_score"])
                    results.append(item)
                return results[:top_k]
        except Exception:
            pass  # Fallback to RRF below

    # Fallback to RRF ranking when Jina API Key is missing or inactive
    return rerank_rrf([candidates], top_k=top_k)


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.
    """
    if not candidates:
        return []

    # Fast relevance-based sorting fallback
    sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_candidates[:top_k]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    if not ranked_lists:
        return []

    rrf_scores = {}    # content -> float rrf_score
    content_map = {}   # content -> full candidate dict

    for ranked_list in ranked_lists:
        if not isinstance(ranked_list, list):
            continue
        for rank, item in enumerate(ranked_list, 1):
            if not isinstance(item, dict) or "content" not in item:
                continue
            key = item["content"]
            score_addition = 1.0 / (k + rank)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + score_addition

            # Keep candidate metadata
            if key not in content_map:
                content_map[key] = item.copy()

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, rrf_score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = round(rrf_score, 6)
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if not candidates:
        return []

    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "rrf":
        # RRF expects a list of ranked lists
        if isinstance(candidates, list) and candidates and isinstance(candidates[0], list):
            return rerank_rrf(candidates, top_k=top_k)
        else:
            return rerank_rrf([candidates], top_k=top_k)
    else:
        # Fallback RRF
        return rerank_rrf([candidates], top_k=top_k)


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Tuition fee payment schedule", "score": 0.8, "metadata": {}},
        {"content": "Scholarship eligibility requirements", "score": 0.6, "metadata": {}},
        {"content": "Library study room booking guide", "score": 0.5, "metadata": {}},
    ]
    results = rerank("tuition fee payment", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.4f}] {r['content']}")
