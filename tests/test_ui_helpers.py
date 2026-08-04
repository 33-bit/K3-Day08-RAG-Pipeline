from src.ui_helpers import build_demo_response, normalise_response, resolve_response


def test_normalise_response_keeps_pipeline_answer_sources_and_origin():
    """Would fail if the UI drops source data returned by Task 10."""
    response = {
        "answer": "Bạn có thể xem chính sách học phí.",
        "sources": [{"content": "Fee policy", "metadata": {"source": "fees.md"}}],
        "retrieval_source": "pageindex",
    }

    assert normalise_response(response) == response


def test_normalise_response_supplies_safe_defaults_for_partial_pipeline_output():
    """Would fail if incomplete pipeline output crashes source rendering."""
    assert normalise_response({"answer": "Chưa có nguồn."}) == {
        "answer": "Chưa có nguồn.",
        "sources": [],
        "retrieval_source": "none",
    }


def test_demo_response_matches_the_pipeline_contract():
    """Would fail if the pre-integration UI cannot render a realistic answer."""
    response = build_demo_response("Điều kiện học bổng là gì?")

    assert "Điều kiện học bổng là gì?" in response["answer"]
    assert response["retrieval_source"] == "hybrid"
    assert len(response["sources"]) == 2
    assert all("content" in source and "metadata" in source for source in response["sources"])


def test_resolve_response_uses_demo_when_generation_is_not_implemented():
    """Would fail if the unfinished Task 10 prevents students using the UI."""
    def unfinished_generation(query: str, top_k: int) -> dict:
        raise NotImplementedError

    response, is_demo = resolve_response("Làm sao đặt phòng học?", 5, unfinished_generation)

    assert is_demo is True
    assert response["sources"]
