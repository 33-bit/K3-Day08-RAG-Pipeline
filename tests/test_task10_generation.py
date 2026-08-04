import copy

import src.task10_generation as task10


CHUNKS = [
    {"content": f"Chunk {index}", "score": 1.0 - index * 0.1, "metadata": {"source": f"doc-{index}.md", "type": "policy"}}
    for index in range(5)
]


def test_reorder_places_the_second_best_chunk_at_the_end_without_mutating_input():
    """Would fail if lost-in-the-middle ordering is changed or mutates retrieval results."""
    original = copy.deepcopy(CHUNKS)

    reordered = task10.reorder_for_llm(CHUNKS)

    assert [chunk["content"] for chunk in reordered] == ["Chunk 0", "Chunk 2", "Chunk 4", "Chunk 3", "Chunk 1"]
    assert CHUNKS == original


def test_format_context_labels_each_document_with_its_citation_source():
    """Would fail if the LLM context loses the source needed for citations."""
    context = task10.format_context([CHUNKS[0]])

    assert "[Document 1 | Source: doc-0.md | Type: policy]" in context
    assert "Chunk 0" in context


def test_generation_returns_a_safe_contract_when_retrieval_is_unavailable(monkeypatch):
    """Would fail if an unfinished Task 9 breaks the chatbot UI."""
    def unavailable_retrieval(query: str, top_k: int) -> list[dict]:
        raise NotImplementedError

    monkeypatch.setattr(task10, "retrieve", unavailable_retrieval)

    assert task10.generate_with_citation("Học phí là bao nhiêu?") == {
        "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
        "sources": [],
        "retrieval_source": "none",
    }


def test_generation_returns_openrouter_answer_with_retrieval_sources(monkeypatch):
    """Would fail if a successful OpenRouter response is discarded by the UI contract."""
    monkeypatch.setattr(task10, "retrieve", lambda query, top_k: [CHUNKS[0]])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(task10, "_call_openrouter", lambda context, query, api_key: "Câu trả lời có [doc-0.md].")

    result = task10.generate_with_citation("Học phí là bao nhiêu?")

    assert result == {
        "answer": "Câu trả lời có [doc-0.md].",
        "sources": [CHUNKS[0]],
        "retrieval_source": "hybrid",
    }


def test_generation_returns_fallback_when_api_key_is_missing(monkeypatch):
    """Would fail if missing credentials cause a crash during the live demo."""
    monkeypatch.setattr(task10, "retrieve", lambda query, top_k: [CHUNKS[0]])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert task10.generate_with_citation("Học phí là bao nhiêu?")["answer"] == (
        "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    )
