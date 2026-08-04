"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_DOC_ID = os.getenv("PAGEINDEX_DOC_ID", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    # TODO: Implement upload
    #
    # Tham khảo: https://github.com/VectifyAI/PageIndex
    #
    # from pageindex.client import PageIndexClient
    #
    # client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    #
    # for md_file in STANDARDIZED_DIR.rglob("*.md"):
    #     # Lưu ý: PageIndex nhận PDF, không nhận .md trực tiếp — có thể cần
    #     # convert markdown sang PDF đơn giản bằng fpdf2 trước khi upload.
    #     resp = client.submit_document(str(pdf_path))
    #     doc_id = resp.get("doc_id") or resp.get("id")
    #     print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
    raise NotImplementedError("Implement upload_documents")


def fetch_pageindex_retrieval(query: str) -> dict:
    """Fetch the raw Cloud response.

    This is the only function that needs replacing when Cloud credentials and
    the final PageIndex SDK/API contract are available.
    """
    if not PAGEINDEX_API_KEY or not PAGEINDEX_DOC_ID:
        return {}

    raise NotImplementedError(
        "Configure the PageIndex Cloud SDK call after confirming its live response schema."
    )


def parse_pageindex_retrieval(retrieval: dict, top_k: int) -> list[dict]:
    """Flatten PageIndex nodes into the retrieval format used across the RAG app."""
    if top_k <= 0:
        return []

    results = []
    for node in retrieval.get("retrieved_nodes", []):
        node_id = node.get("node_id", "")
        for group in node.get("relevant_contents", []):
            if not isinstance(group, list):
                continue
            for item in group:
                content = str(item.get("relevant_content", "")).strip()
                if not content:
                    continue

                rank = len(results) + 1
                results.append(
                    {
                        "content": content,
                        "score": round(1.0 / rank, 6),
                        "metadata": {
                            "section": item.get("section_title", ""),
                            "node_id": node_id,
                        },
                        "source": "pageindex",
                    }
                )
                if len(results) == top_k:
                    return results
    return results


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    try:
        retrieval = fetch_pageindex_retrieval(query)
    except NotImplementedError:
        return []
    return parse_pageindex_retrieval(retrieval, top_k)


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("tuition fee payment methods", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
