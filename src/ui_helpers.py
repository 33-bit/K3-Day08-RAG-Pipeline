"""Small, dependency-free helpers shared by the Streamlit interface."""


def normalise_response(response: dict) -> dict:
    """Return the stable response shape consumed by the chat UI."""
    return {
        "answer": response.get("answer", "Chưa thể trả lời."),
        "sources": response.get("sources", []),
        "retrieval_source": response.get("retrieval_source", "none"),
    }


def format_score(score: float) -> str:
    """Format retrieval scores consistently for display in the UI."""
    return f"{float(score):.4f}"


def build_demo_response(query: str) -> dict:
    """Provide a realistic response while the RAG pipeline is unavailable."""
    return {
        "answer": (
            f"Đây là câu trả lời minh hoạ cho: **{query}**. "
            "Khi pipeline hoàn thiện, UniHelp sẽ trả lời dựa trên tài liệu chính thức."
        ),
        "sources": [
            {
                "content": "Thông tin chính sách và hướng dẫn dịch vụ sinh viên.",
                "score": 0.91,
                "metadata": {"source": "student-services.md", "type": "policy"},
            },
            {
                "content": "Hướng dẫn liên hệ và các bước thực hiện dịch vụ.",
                "score": 0.84,
                "metadata": {"source": "student-guide.md", "type": "guide"},
            },
        ],
        "retrieval_source": "hybrid",
    }


def resolve_response(query: str, top_k: int, generator) -> tuple[dict, bool]:
    """Run generation, or return a demo payload while Task 10 is unfinished."""
    try:
        return normalise_response(generator(query, top_k=top_k)), False
    except NotImplementedError:
        return build_demo_response(query), True
