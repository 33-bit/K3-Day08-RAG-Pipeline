"""Behavior tests for the Task 6 sparse-retrieval module."""

import src.task6_lexical_search as task6


SAMPLE_CORPUS = [
    {
        "content": "Tuition fee payment is due before registration.",
        "metadata": {"source": "fees.md"},
    },
    {
        "content": "The library lends laptops and reserves study rooms.",
        "metadata": {"source": "library.md"},
    },
    {
        "content": "Scholarship eligibility depends on academic results.",
        "metadata": {"source": "scholarships.md"},
    },
]


def test_bm25_returns_the_exact_keyword_match_first(monkeypatch):
    """Would fail if BM25 does not score exact keyword matches."""
    monkeypatch.setattr(task6, "CORPUS", SAMPLE_CORPUS)

    results = task6.lexical_search("tuition fee", top_k=2)

    assert results[0]["metadata"] == {"source": "fees.md"}
    assert results[0]["score"] > 0
    assert results == sorted(results, key=lambda result: result["score"], reverse=True)


def test_tfidf_returns_the_exact_keyword_match_first(monkeypatch):
    """Would fail if TF-IDF does not score exact keyword matches."""
    monkeypatch.setattr(task6, "CORPUS", SAMPLE_CORPUS)

    results = task6.tfidf_search("library study rooms", top_k=2)

    assert results[0]["metadata"] == {"source": "library.md"}
    assert results[0]["score"] > 0
    assert results == sorted(results, key=lambda result: result["score"], reverse=True)


def test_sparse_searches_return_no_results_for_an_empty_corpus(monkeypatch):
    """Would fail if an empty corpus raises instead of returning an empty result set."""
    monkeypatch.setattr(task6, "CORPUS", [])

    assert task6.lexical_search("tuition fee") == []
    assert task6.tfidf_search("tuition fee") == []


def test_bm25_index_uses_the_required_term_saturation_value():
    """Would fail if the BM25 k1 configuration changes from the task requirement."""
    index = task6.build_bm25_index(SAMPLE_CORPUS)

    assert index.k1 == 1.5
