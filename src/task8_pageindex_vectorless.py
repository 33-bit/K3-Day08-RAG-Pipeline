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
import textwrap
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_DOC_ID = os.getenv("PAGEINDEX_DOC_ID", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
PAGEINDEX_DIR = Path(__file__).parent.parent / "data" / "pageindex"


def markdown_to_pdf(markdown_path: Path, output_path: Path | None = None) -> Path:
    """Create a PageIndex-uploadable PDF from one standardized Markdown file.

    The bundled fpdf2 core font is Latin-1 only, so unsupported Unicode characters
    are removed deliberately. The original Markdown remains the lossless source.
    """
    from fpdf import FPDF

    markdown_path = Path(markdown_path)
    output_path = output_path or PAGEINDEX_DIR / f"{markdown_path.stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    safe_text = markdown_path.read_text(encoding="utf-8").encode(
        "latin-1", errors="ignore"
    ).decode("latin-1")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in safe_text.splitlines():
        line = line.lstrip("# ").strip()
        if not line:
            pdf.ln(4)
            continue
        for wrapped_line in textwrap.wrap(
            line, width=95, break_long_words=True, break_on_hyphens=False
        ) or [""]:
            pdf.multi_cell(180, 5, wrapped_line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(output_path))
    return output_path


def prepare_pageindex_pdfs() -> list[Path]:
    """Convert all standardized Markdown documents without uploading them."""
    return [markdown_to_pdf(path) for path in sorted(STANDARDIZED_DIR.rglob("*.md"))]


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
