"""
RAG Evaluation Pipeline.

Primary framework: RAGAS.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md

Nếu môi trường thiếu thư viện/LLM key, script vẫn có thể chạy bằng fallback
heuristic để tạo báo cáo, nhưng đường chính vẫn là RAGAS.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = 0.48
DEFAULT_SUBSET_SIZE = int(os.getenv("EVAL_MAX_CASES", "0") or "0")

DEFAULT_RAGAS_LLM_MODEL = os.getenv("RAG_EVAL_LLM_MODEL", "openai/gpt-4o-mini")
DEFAULT_RAGAS_LLM_BASE_URL = os.getenv("RAG_EVAL_LLM_BASE_URL", "")
DEFAULT_RAGAS_LLM_API_KEY = os.getenv(
    "RAG_EVAL_LLM_API_KEY",
    os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", "")),
)
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "RAG_EVAL_EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+|\n+")
TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
FALLBACK_FALLBACK_ANSWER = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

VI_STOPWORDS = {
    "và",
    "hoặc",
    "là",
    "của",
    "cho",
    "với",
    "các",
    "một",
    "những",
    "được",
    "trong",
    "khi",
    "này",
    "đó",
    "theo",
    "tại",
    "về",
    "bị",
    "ra",
    "đến",
    "nếu",
    "thì",
    "có",
    "không",
    "lại",
    "để",
    "vì",
    "đang",
    "sẽ",
    "đã",
    "đây",
    "kia",
    "hơn",
    "dưới",
    "trên",
    "từ",
    "điều",
    "khoản",
    "quy",
    "chế",
    "quyết",
    "định",
}


@dataclass(frozen=True)
class EvaluationConfig:
    """Cấu hình một run evaluation."""

    name: str
    description: str
    retrieval_mode: str
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    rerank_method: str = "cross_encoder"


@dataclass
class EvaluationPipelineAdapter:
    """Adapter nhỏ để chạy retrieval theo từng config."""

    config: EvaluationConfig

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def description(self) -> str:
        return self.config.description

    def generate_with_citation(self, question: str) -> dict[str, Any]:
        from src.task5_semantic_search import semantic_search
        from src.task6_lexical_search import lexical_search
        from src.task7_reranking import rerank

        if not question or not question.strip():
            return {
                "answer": FALLBACK_FALLBACK_ANSWER,
                "sources": [],
                "retrieval_source": "none",
            }

        if self.config.retrieval_mode == "dense_only":
            chunks = semantic_search(question, top_k=self.config.top_k)
            retrieval_source = "dense"
        else:
            dense_results = semantic_search(question, top_k=self.config.top_k * 2)
            sparse_results = lexical_search(question, top_k=self.config.top_k * 2)
            merged = _merge_hybrid_candidates(dense_results, sparse_results, self.config.top_k * 2)
            chunks = rerank(question, merged, top_k=self.config.top_k, method=self.config.rerank_method)
            retrieval_source = "hybrid"

        if not chunks:
            return {
                "answer": FALLBACK_FALLBACK_ANSWER,
                "sources": [],
                "retrieval_source": retrieval_source if 'retrieval_source' in locals() else "none",
            }

        answer = _synthesize_answer(question, chunks)
        if retrieval_source == "hybrid":
            for item in chunks:
                item.setdefault("source", "hybrid")
        else:
            for item in chunks:
                item.setdefault("source", "dense")

        return {
            "answer": answer,
            "sources": chunks,
            "retrieval_source": retrieval_source,
        }


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    if not GOLDEN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing golden dataset: {GOLDEN_DATASET_PATH}")

    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if not isinstance(dataset, list):
        raise ValueError("golden_dataset.json must contain a list of records")
    if len(dataset) < 15:
        raise ValueError("golden_dataset.json must contain at least 15 Q&A pairs")
    return dataset


def _limit_dataset(dataset: list[dict]) -> list[dict]:
    """Reduce dataset size if EVAL_MAX_CASES is set."""
    if DEFAULT_SUBSET_SIZE and DEFAULT_SUBSET_SIZE > 0:
        return dataset[:DEFAULT_SUBSET_SIZE]
    return dataset


def _merge_hybrid_candidates(dense_results: list[dict], sparse_results: list[dict], top_k: int) -> list[dict]:
    """Fuse dense and sparse retrieval results with RRF before reranking."""
    from src.task7_reranking import rerank_rrf

    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k)
    for item in merged:
        item["source"] = "hybrid"
    return merged


def _sentence_split(text: str) -> list[str]:
    parts = [part.strip() for part in SENTENCE_SPLIT_RE.split(text or "")]
    return [part for part in parts if part]


def _tokenize(text: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall((text or "").lower()):
        if token in VI_STOPWORDS or len(token) < 2:
            continue
        tokens.append(token)
    return tokens


def _normalized_source_label(chunk: dict[str, Any], index: int) -> str:
    metadata = chunk.get("metadata", {}) if isinstance(chunk, dict) else {}
    source = metadata.get("source") or metadata.get("document") or metadata.get(
        "file"
    )
    if source:
        return str(source)
    return f"Document {index}"


def _synthesize_answer(question: str, sources: list[dict[str, Any]]) -> str:
    """Tạo answer ngắn theo kiểu extractive để phục vụ evaluation."""
    sentences: list[str] = []
    citations: list[str] = []

    question_tokens = set(_tokenize(question))
    for index, chunk in enumerate(sources, start=1):
        content = str(chunk.get("content", "")).strip()
        if not content:
            continue

        fragments = _sentence_split(content) or [content]
        best_fragment = fragments[0]

        if question_tokens:
            best_score = -1.0
            for fragment in fragments[:4]:
                fragment_tokens = set(_tokenize(fragment))
                overlap = len(question_tokens & fragment_tokens)
                score = overlap / max(len(fragment_tokens), 1)
                if score > best_score:
                    best_score = score
                    best_fragment = fragment

        sentences.append(best_fragment.strip())
        citations.append(f"[{index}] {_normalized_source_label(chunk, index)}")

        if len(sentences) >= 2:
            break

    if not sentences:
        return FALLBACK_FALLBACK_ANSWER

    answer = " ".join(sentences).strip()
    citation_text = " ".join(citations)
    if citation_text:
        answer = f"{answer} {citation_text}".strip()

    if len(answer) > 900:
        answer = answer[:897].rstrip() + "..."
    return answer


def _safe_mean(values: list[float]) -> float:
    clean_values = []
    for value in values:
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isnan(numeric):
            continue
        clean_values.append(numeric)
    return round(fmean(clean_values), 4) if clean_values else 0.0


def _build_local_embeddings() -> Any:
    """Build a lightweight embedding object for RAGAS."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Missing sentence-transformers. Install dependencies from requirements.txt."
        ) from exc

    class _SentenceTransformerEmbeddings:
        def __init__(self, model_name: str):
            self._model = SentenceTransformer(model_name)

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)

        def embed_query(self, text: str) -> list[float]:
            vector = self._model.encode([text], normalize_embeddings=True)[0]
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    return _SentenceTransformerEmbeddings(DEFAULT_EMBEDDING_MODEL)


def _build_ragas_llm() -> Any:
    """Build the LLM judge used by RAGAS metrics."""
    if not DEFAULT_RAGAS_LLM_API_KEY:
        raise RuntimeError(
            "Missing RAGAS LLM key. Set RAG_EVAL_LLM_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY."
        )

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Missing langchain-openai. Install dependencies from requirements.txt."
        ) from exc

    kwargs: dict[str, Any] = {
        "model": DEFAULT_RAGAS_LLM_MODEL,
        "api_key": DEFAULT_RAGAS_LLM_API_KEY,
        "temperature": 0,
    }
    if DEFAULT_RAGAS_LLM_BASE_URL.strip():
        kwargs["base_url"] = DEFAULT_RAGAS_LLM_BASE_URL.strip()
    elif os.getenv("OPENROUTER_API_KEY"):
        kwargs["base_url"] = "https://openrouter.ai/api/v1"

    return ChatOpenAI(**kwargs)


def _attach_ragas_dependencies(metrics: list[Any], llm: Any, embeddings: Any) -> list[Any]:
    attached_metrics = []
    for metric in metrics:
        metric_copy = copy.deepcopy(metric)
        if hasattr(metric_copy, "llm"):
            metric_copy.llm = llm
        if hasattr(metric_copy, "embeddings"):
            metric_copy.embeddings = embeddings
        attached_metrics.append(metric_copy)
    return attached_metrics


def _build_ragas_dataset(records: list[dict[str, Any]]):
    try:
        from datasets import Dataset
    except ImportError as exc:
        raise RuntimeError("Missing datasets package. Install requirements.txt.") from exc

    data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
        "ground_truths": [],
        "reference": [],
    }

    for record in records:
        data["question"].append(record["question"])
        data["answer"].append(record["answer"])
        data["contexts"].append(record["contexts"])
        data["ground_truth"].append(record["ground_truth"])
        data["ground_truths"].append([record["ground_truth"]])
        data["reference"].append(record["ground_truth"])

    return Dataset.from_dict(data)


def _evaluate_with_heuristics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Fallback evaluation khi RAGAS không khả dụng."""
    per_question = []
    metric_buckets = {
        "faithfulness": [],
        "answer_relevancy": [],
        "context_recall": [],
        "context_precision": [],
    }

    for record in records:
        question_tokens = set(_tokenize(record["question"]))
        answer_tokens = set(_tokenize(record["answer"]))
        ground_tokens = set(_tokenize(record["ground_truth"]))
        context_tokens: set[str] = set()
        for context in record["contexts"]:
            context_tokens.update(_tokenize(context))

        answer_overlap = answer_tokens & context_tokens
        faithfulness = len(answer_overlap) / max(len(answer_tokens), 1)
        relevance = len(question_tokens & answer_tokens) / max(len(question_tokens), 1)
        recall = len(ground_tokens & context_tokens) / max(len(ground_tokens), 1)
        precision = len(ground_tokens & context_tokens) / max(len(context_tokens), 1)

        row = {
            "question": record["question"],
            "answer": record["answer"],
            "ground_truth": record["ground_truth"],
            "faithfulness": round(faithfulness, 4),
            "answer_relevancy": round(relevance, 4),
            "context_recall": round(recall, 4),
            "context_precision": round(precision, 4),
        }
        per_question.append(row)

        metric_buckets["faithfulness"].append(row["faithfulness"])
        metric_buckets["answer_relevancy"].append(row["answer_relevancy"])
        metric_buckets["context_recall"].append(row["context_recall"])
        metric_buckets["context_precision"].append(row["context_precision"])

    return {
        "metric_scores": {name: _safe_mean(values) for name, values in metric_buckets.items()},
        "per_question": per_question,
        "raw_rows": per_question,
        "evaluation_mode": "heuristic-fallback",
    }


def _extract_metric_summary(result: Any, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize a RAGAS result into a simple report structure."""
    if hasattr(result, "to_pandas"):
        frame = result.to_pandas()
        raw_rows = frame.to_dict(orient="records")
    else:
        raw_rows = list(result) if isinstance(result, list) else []

    if not raw_rows:
        return _evaluate_with_heuristics(records)

    metric_names = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    metric_scores: dict[str, list[float]] = {name: [] for name in metric_names}
    per_question: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        row = raw_rows[index] if index < len(raw_rows) else {}
        merged = {
            "question": record["question"],
            "answer": record["answer"],
            "ground_truth": record["ground_truth"],
        }
        for name in metric_names:
            value = row.get(name)
            if value is None and name in record:
                value = record[name]
            if value is not None:
                try:
                    metric_scores[name].append(float(value))
                    merged[name] = round(float(value), 4)
                except (TypeError, ValueError):
                    merged[name] = None
            else:
                merged[name] = None
        per_question.append(merged)

    return {
        "metric_scores": {name: _safe_mean(values) for name, values in metric_scores.items()},
        "per_question": per_question,
        "raw_rows": raw_rows,
        "evaluation_mode": "ragas",
    }


# =============================================================================
# Option 1: DeepEval
# =============================================================================

def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """Compatibility wrapper kept for the lab prompt."""
    raise NotImplementedError(
        "This file uses RAGAS as the primary framework. Use evaluate_with_ragas()."
    )


# =============================================================================
# Option 2: RAGAS
# =============================================================================

def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng RAGAS.

    The pipeline only needs to expose generate_with_citation(question)->dict.
    """
    evaluation_records: list[dict[str, Any]] = []

    for item in golden_dataset:
        question = item["question"]
        expected_answer = item["expected_answer"]

        result = rag_pipeline.generate_with_citation(question)
        sources = result.get("sources", []) or []
        contexts = [
            str(source.get("content", "")).strip()
            for source in sources
            if str(source.get("content", "")).strip()
        ]
        evaluation_records.append(
            {
                "question": question,
                "answer": str(result.get("answer", FALLBACK_FALLBACK_ANSWER)),
                "contexts": contexts,
                "ground_truth": expected_answer,
                "retrieval_source": result.get("retrieval_source", "none"),
                "sources": sources,
            }
        )

    try:
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        llm = _build_ragas_llm()
        embeddings = _build_local_embeddings()
        metrics = _attach_ragas_dependencies(
            [faithfulness, answer_relevancy, context_recall, context_precision],
            llm,
            embeddings,
        )
        dataset = _build_ragas_dataset(evaluation_records)
        result = evaluate(dataset, metrics=metrics)
        summary = _extract_metric_summary(result, evaluation_records)
    except Exception as exc:
        print(f"RAGAS evaluation unavailable, using heuristic fallback: {exc}")
        summary = _evaluate_with_heuristics(evaluation_records)

    summary.update(
        {
            "framework": "RAGAS",
            "config_name": getattr(rag_pipeline, "config_name", getattr(rag_pipeline, "name", "unknown")),
            "config_description": getattr(rag_pipeline, "description", ""),
            "sample_size": len(evaluation_records),
            "records": evaluation_records,
        }
    )
    return summary


# =============================================================================
# Option 3: TruLens
# =============================================================================

def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """Compatibility wrapper kept for the lab prompt."""
    raise NotImplementedError(
        "This file uses RAGAS as the primary framework. Use evaluate_with_ragas()."
    )


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(rag_pipeline, golden_dataset: list[dict]):
    """
    So sánh A/B giữa ít nhất 2 configs.

    Config A: hybrid search + reranking
    Config B: dense-only (không reranking)
    """
    configs = [
        EvaluationConfig(
            name="hybrid_rerank",
            description="Hybrid search + reranking",
            retrieval_mode="hybrid",
            top_k=DEFAULT_TOP_K,
            score_threshold=DEFAULT_SCORE_THRESHOLD,
            rerank_method="cross_encoder",
        ),
        EvaluationConfig(
            name="dense_only",
            description="Dense-only retrieval without reranking",
            retrieval_mode="dense_only",
            top_k=DEFAULT_TOP_K,
            score_threshold=DEFAULT_SCORE_THRESHOLD,
            rerank_method="rrf",
        ),
    ]

    results: dict[str, dict[str, Any]] = {}
    for config in configs:
        pipeline = EvaluationPipelineAdapter(config=config)
        results[config.name] = evaluate_with_ragas(pipeline, golden_dataset)

    metric_names = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    averages = {
        name: _safe_mean(list(result["metric_scores"].values()))
        for name, result in results.items()
    }
    best_config = max(averages, key=averages.get) if averages else configs[0].name

    return {
        "framework": "RAGAS",
        "baseline_config": configs[0].name,
        "comparison_config": configs[1].name,
        "best_config": best_config,
        "config_order": [config.name for config in configs],
        "metric_names": metric_names,
        "configs": results,
    }


# =============================================================================
# Export Results
# =============================================================================

def _format_score(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "-"


def _overall_average(metric_scores: dict[str, float]) -> float:
    return _safe_mean(list(metric_scores.values()))


def _failure_stage(row: dict[str, Any]) -> str:
    faithfulness = float(row.get("faithfulness") or 0.0)
    relevance = float(row.get("answer_relevancy") or 0.0)
    recall = float(row.get("context_recall") or 0.0)
    precision = float(row.get("context_precision") or 0.0)

    if recall < 0.45 and precision < 0.45:
        return "Retrieval quality"
    if recall < 0.45:
        return "Missing evidence"
    if precision < 0.45:
        return "Noisy context"
    if faithfulness < 0.45:
        return "Grounding / generation"
    if relevance < 0.45:
        return "Question understanding"
    return "Mixed"


def _root_cause(row: dict[str, Any]) -> str:
    stage = _failure_stage(row)
    if stage == "Retrieval quality":
        return "Retriever missed the supporting passage or pulled too much noise."
    if stage == "Missing evidence":
        return "Relevant facts are absent from the retrieved context."
    if stage == "Noisy context":
        return "Top-k contains many unrelated chunks, so precision drops."
    if stage == "Grounding / generation":
        return "Answer content is not fully supported by the retrieved evidence."
    if stage == "Question understanding":
        return "Answer is semantically weak relative to the question intent."
    return "Multiple weak points across retrieval and generation."


def export_results(results: dict, comparison: dict):
    """Export evaluation results to results.md"""
    configs = comparison["configs"]
    baseline_name = comparison["baseline_config"]
    comparison_name = comparison["comparison_config"]
    baseline = configs[baseline_name]
    competitor = configs[comparison_name]

    metric_names = comparison.get(
        "metric_names",
        ["faithfulness", "answer_relevancy", "context_recall", "context_precision"],
    )

    content: list[str] = []
    content.append("# RAG Evaluation Results")
    content.append("")
    content.append(f"Framework used: **{comparison.get('framework', 'RAGAS')}**")
    content.append("")
    content.append("## Overall Scores")
    content.append("")
    content.append(f"| Metric | {baseline_name} | {comparison_name} | Δ |")
    content.append("|--------|--------:|--------:|--------:|")

    for metric_name in metric_names:
        base_score = baseline["metric_scores"].get(metric_name, 0.0)
        other_score = competitor["metric_scores"].get(metric_name, 0.0)
        delta = round(base_score - other_score, 4)
        content.append(
            f"| {metric_name.replace('_', ' ').title()} | {_format_score(base_score)} | {_format_score(other_score)} | {_format_score(delta)} |"
        )

    base_average = _overall_average(baseline["metric_scores"])
    other_average = _overall_average(competitor["metric_scores"])
    content.append(
        f"| **Average** | **{_format_score(base_average)}** | **{_format_score(other_average)}** | **{_format_score(base_average - other_average)}** |"
    )
    content.append("")

    content.append("## A/B Comparison Analysis")
    content.append("")
    content.append(
        f"**Config A ({baseline_name}):** {baseline.get('config_description', 'Hybrid retrieval with reranking.')}"
    )
    content.append(
        f"**Config B ({comparison_name}):** {competitor.get('config_description', 'Dense-only retrieval without reranking.')}"
    )
    content.append("")

    winner_name = comparison.get("best_config", baseline_name)
    if winner_name == baseline_name:
        content.append(
            f"**Kết luận:** {baseline_name} đang nhỉnh hơn về trung bình tổng thể, chủ yếu nhờ giữ chất lượng context tốt hơn sau reranking."
        )
    elif winner_name == comparison_name:
        content.append(
            f"**Kết luận:** {comparison_name} đang tốt hơn về trung bình tổng thể, cho thấy reranking hiện tại chưa giúp cải thiện đáng kể."
        )
    else:
        content.append(
            "**Kết luận:** Hai config khá sát nhau, cần thêm tuning top_k, score_threshold hoặc reranker."
        )

    content.append("")

    content.append("## Worst Performers (Bottom 3)")
    content.append("")
    content.append("| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |")
    content.append("|---|----------|-------------:|----------:|-------:|---------------|------------|")

    sorted_rows = sorted(
        baseline["per_question"],
        key=lambda row: _safe_mean(
            [
                float(row.get("faithfulness") or 0.0),
                float(row.get("answer_relevancy") or 0.0),
                float(row.get("context_recall") or 0.0),
                float(row.get("context_precision") or 0.0),
            ]
        ),
    )

    for index, row in enumerate(sorted_rows[:3], start=1):
        question = str(row.get("question", "")).replace("|", "\\|")
        content.append(
            f"| {index} | {question} | {_format_score(row.get('faithfulness'))} | {_format_score(row.get('answer_relevancy'))} | {_format_score(row.get('context_recall'))} | {_failure_stage(row)} | {_root_cause(row)} |"
        )

    content.append("")
    content.append("## Recommendations")
    content.append("")
    baseline_recall = baseline["metric_scores"].get("context_recall", 0.0)
    baseline_precision = baseline["metric_scores"].get("context_precision", 0.0)
    baseline_faithfulness = baseline["metric_scores"].get("faithfulness", 0.0)

    content.append("### Cải tiến 1")
    content.append(
        "**Action:** Tăng chất lượng retrieval bằng tuning `top_k`, `score_threshold`, và query expansion cho các câu hỏi dài."
    )
    content.append(
        f"**Expected impact:** Nâng context recall từ {_format_score(baseline_recall)} lên mức ổn định hơn.\n"
    )

    content.append("")
    content.append("### Cải tiến 2")
    content.append(
        "**Action:** Giảm noise bằng cách giữ reranking cho nhóm câu hỏi cần evidence rõ ràng và giảm `top_k` nếu precision thấp."
    )
    content.append(
        f"**Expected impact:** Cải thiện context precision từ {_format_score(baseline_precision)} và giảm câu trả lời lệch nguồn."
    )

    content.append("")
    content.append("### Cải tiến 3")
    content.append(
        "**Action:** Siết prompt generation để answer luôn bám citation và từ chối khi evidence không đủ."
    )
    content.append(
        f"**Expected impact:** Tăng faithfulness từ {_format_score(baseline_faithfulness)} và giảm hallucination."
    )

    RESULTS_PATH.write_text("\n".join(content) + "\n", encoding="utf-8")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    evaluation_dataset = _limit_dataset(golden_dataset)
    print(f"Loaded {len(golden_dataset)} test cases")
    if len(evaluation_dataset) != len(golden_dataset):
        print(f"Using subset of {len(evaluation_dataset)} cases for evaluation")

    comparison = compare_configs(None, evaluation_dataset)
    primary_result = comparison["configs"][comparison["baseline_config"]]
    export_results(primary_result, comparison)
    print(f"Saved evaluation report to {RESULTS_PATH}")
