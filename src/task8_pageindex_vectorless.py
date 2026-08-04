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

import json
import time
import os
import textwrap
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_DOC_ID = os.getenv("PAGEINDEX_DOC_ID", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
PAGEINDEX_DIR = Path(__file__).parent.parent / "data" / "pageindex"
DOC_IDS_PATH = PAGEINDEX_DIR / "doc_ids.json"

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
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Missing PAGEINDEX_API_KEY in .env")

    from pageindex.client import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    pdf_paths = prepare_pageindex_pdfs()

    uploaded = []

    for pdf_path in pdf_paths:
        print(f"Uploading: {pdf_path.name}")
        resp = client.submit_document(str(pdf_path))

        doc_id = resp.get("doc_id") or resp.get("id") or resp.get("document_id")
        if not doc_id:
            raise RuntimeError(f"Cannot find doc_id in response: {resp}")

        uploaded.append({"name": pdf_path.name, "doc_id": doc_id})
        print(f"Uploaded: {pdf_path.name} -> {doc_id}")

    DOC_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_IDS_PATH.write_text(
        json.dumps(uploaded, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return uploaded

def _load_uploaded_documents():
    if DOC_IDS_PATH.exists():
        return json.loads(DOC_IDS_PATH.read_text(encoding="utf-8"))
    return upload_documents()


def _wait_for_retrieval(client, retrieval_id: str, max_wait_seconds: int = 90):
    start = time.time()

    while time.time() - start < max_wait_seconds:
        retrieval = client.get_retrieval(retrieval_id)

        status = str(retrieval.get("status", "")).lower()
        if retrieval.get("retrieved_nodes"):
            return retrieval

        if status in {"completed", "complete", "succeeded", "success"}:
            return retrieval

        if status in {"failed", "error"}:
            raise RuntimeError(f"PageIndex retrieval failed: {retrieval}")

        time.sleep(3)

    raise TimeoutError(f"PageIndex retrieval timeout: {retrieval_id}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if not query or not query.strip():
        return []

    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Missing PAGEINDEX_API_KEY in .env")

    from pageindex.client import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    documents = _load_uploaded_documents()

    results = []
    rank = 1

    for doc in documents:
        resp = client.submit_query(doc_id=doc["doc_id"], query=query)
        retrieval_id = resp.get("retrieval_id") or resp.get("id")

        if not retrieval_id:
            continue

        retrieval = _wait_for_retrieval(client, retrieval_id)

        for node in retrieval.get("retrieved_nodes", []):
            for group in node.get("relevant_contents", []):
                if isinstance(group, dict):
                    group = [group]

                for item in group:
                    content = item.get("relevant_content", "") if isinstance(item, dict) else str(item)

                    if not content.strip():
                        continue

                    results.append({
                        "content": content.strip(),
                        "score": round(1.0 / rank, 4),
                        "metadata": {
                            "doc_id": doc["doc_id"],
                            "document": doc["name"],
                            "rank": rank,
                        },
                        "source": "pageindex",
                    })

                    rank += 1

                    if len(results) >= top_k:
                        break

                if len(results) >= top_k:
                    break

            if len(results) >= top_k:
                break

        if len(results) >= top_k:
            break

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

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
