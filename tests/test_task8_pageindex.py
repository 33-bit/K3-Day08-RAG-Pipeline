import src.task8_pageindex_vectorless as task8


RETRIEVAL_RESPONSE = {
    "retrieved_nodes": [
        {
            "node_id": "chapter-1",
            "relevant_contents": [
                [
                    {"section_title": "Học phí", "relevant_content": "Học phí được thanh toán theo học kỳ."},
                    {"section_title": "Thanh toán", "relevant_content": "Sinh viên có thể thanh toán trực tuyến."},
                ],
                [{"section_title": "Bỏ qua", "relevant_content": ""}],
            ],
        }
    ]
}


def test_parse_retrieval_returns_rag_compatible_pageindex_results():
    """Would fail if PageIndex content is not normalised for Task 9 and the UI."""
    results = task8.parse_pageindex_retrieval(RETRIEVAL_RESPONSE, top_k=5)

    assert results == [
        {
            "content": "Học phí được thanh toán theo học kỳ.",
            "score": 1.0,
            "metadata": {"section": "Học phí", "node_id": "chapter-1"},
            "source": "pageindex",
        },
        {
            "content": "Sinh viên có thể thanh toán trực tuyến.",
            "score": 0.5,
            "metadata": {"section": "Thanh toán", "node_id": "chapter-1"},
            "source": "pageindex",
        },
    ]


def test_pageindex_search_uses_the_adapter_and_honours_top_k(monkeypatch):
    """Would fail if the public search function bypasses the cloud adapter."""
    monkeypatch.setattr(task8, "fetch_pageindex_retrieval", lambda query: RETRIEVAL_RESPONSE)

    results = task8.pageindex_search("học phí", top_k=1)

    assert results == [
        {
            "content": "Học phí được thanh toán theo học kỳ.",
            "score": 1.0,
            "metadata": {"section": "Học phí", "node_id": "chapter-1"},
            "source": "pageindex",
        }
    ]


def test_pageindex_search_returns_empty_list_without_cloud_configuration(monkeypatch):
    """Would fail if missing credentials break the RAG fallback path."""
    monkeypatch.setattr(task8, "PAGEINDEX_API_KEY", "")
    monkeypatch.setattr(task8, "PAGEINDEX_DOC_ID", "")

    assert task8.pageindex_search("học phí") == []
