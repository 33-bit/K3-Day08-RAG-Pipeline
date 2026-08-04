"""Run a four-metric RAGAS evaluation over the 20-question golden dataset."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from sklearn.feature_extraction.text import HashingVectorizer

from src.task6_lexical_search import lexical_search


load_dotenv()

EVALUATION_DIR = Path(__file__).parent
GOLDEN_DATASET_PATH = EVALUATION_DIR / "golden_dataset.json"
RESULTS_PATH = EVALUATION_DIR / "results.md"
RAW_RESULTS_PATH = EVALUATION_DIR / "ragas_results.json"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
JUDGE_MODEL = os.getenv("RAGAS_MODEL", "openai/gpt-4o-mini")
TOP_K = 5

METRIC_COLUMNS = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer Relevance",
    "context_recall": "Context Recall",
    "context_precision": "Context Precision",
}


class LocalHashEmbeddings(Embeddings):
    """Stateless local embeddings suitable for RAGAS similarity calculations."""

    def __init__(self, dimensions: int = 2048):
        self.vectorizer = HashingVectorizer(
            n_features=dimensions,
            alternate_sign=False,
            analyzer="char_wb",
            ngram_range=(2, 5),
            norm="l2",
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.vectorizer.transform(texts).toarray().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def load_golden_dataset() -> list[dict]:
    data = json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))
    if len(data) != 20:
        raise ValueError(f"Golden dataset must contain 20 records, found {len(data)}")
    required = {"question", "expected_answer", "expected_context"}
    if not all(required <= item.keys() for item in data):
        raise ValueError(f"Every record must contain: {sorted(required)}")
    return data


def build_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in .env")
    return ChatOpenAI(
        model=JUDGE_MODEL,
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
        max_retries=3,
        timeout=120,
    )


def generate_evaluation_data(golden_dataset: list[dict], llm: ChatOpenAI) -> dict:
    """Retrieve local evidence and generate one grounded answer per question."""
    data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for index, item in enumerate(golden_dataset, start=1):
        retrieved = lexical_search(item["question"], top_k=TOP_K)
        contexts = [result["content"] for result in retrieved]
        context_text = "\n\n---\n\n".join(contexts)
        prompt = (
            "Bạn là trợ lý hỏi đáp về quy định của Đại học Bách khoa Hà Nội. "
            "Chỉ trả lời bằng thông tin trong NGỮ CẢNH, không bịa đặt. "
            "Nếu không đủ dữ kiện, hãy nói không thể xác minh.\n\n"
            f"NGỮ CẢNH:\n{context_text}\n\n"
            f"CÂU HỎI: {item['question']}\n\nTRẢ LỜI:"
        )
        answer = str(llm.invoke(prompt).content).strip()

        data["question"].append(item["question"])
        data["answer"].append(answer)
        data["contexts"].append(contexts)
        data["ground_truth"].append(item["expected_answer"])
        print(f"Generated {index:02d}/{len(golden_dataset)}")

    return data


def evaluate_with_ragas(eval_data: dict, llm: ChatOpenAI):
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )
    from ragas.run_config import RunConfig

    dataset = Dataset.from_dict(eval_data)
    return evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=LocalHashEmbeddings(),
        run_config=RunConfig(timeout=120, max_retries=3, max_workers=1),
        raise_exceptions=False,
    )


def _safe_mean(values) -> float:
    numeric = np.asarray(values, dtype=float)
    return float(np.nanmean(numeric)) if not np.isnan(numeric).all() else float("nan")


def export_results(frame) -> None:
    rows = frame.to_dict(orient="records")
    RAW_RESULTS_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    averages = {column: _safe_mean(frame[column]) for column in METRIC_COLUMNS}
    overall = _safe_mean(list(averages.values()))
    per_row_scores = frame[list(METRIC_COLUMNS)].mean(axis=1, skipna=True)
    worst_indices = per_row_scores.nsmallest(3).index

    lines = [
        "# RAGAS Evaluation Results",
        "",
        "## Run Information",
        "",
        f"- Evaluated at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Framework: RAGAS 0.1.21",
        f"- Judge model: `{JUDGE_MODEL}` via OpenRouter",
        f"- Dataset: 20 golden Q&A records",
        f"- Retrieval: BM25, top_k={TOP_K}",
        "",
        "## Overall Scores",
        "",
        "| Metric | Score |",
        "|---|---:|",
    ]
    for column, label in METRIC_COLUMNS.items():
        lines.append(f"| {label} | {averages[column]:.4f} |")
    lines.extend([f"| **Average** | **{overall:.4f}** |", ""])

    lines.extend([
        "## Worst Performers (Bottom 3)",
        "",
        "| # | Question | Faithfulness | Relevance | Recall | Precision |",
        "|---:|---|---:|---:|---:|---:|",
    ])
    for rank, row_index in enumerate(worst_indices, start=1):
        row = frame.loc[row_index]
        question = str(row["question"]).replace("|", "\\|")
        values = [row[column] for column in METRIC_COLUMNS]
        rendered = ["N/A" if np.isnan(float(value)) else f"{float(value):.4f}" for value in values]
        lines.append(f"| {rank} | {question} | {' | '.join(rendered)} |")

    lines.extend([
        "",
        "## Recommendations",
        "",
        "1. Điều chỉnh tokenizer BM25 cho tiếng Việt và tăng kích thước đoạn khi Context Recall thấp.",
        "2. Dùng hybrid dense + BM25 và reranking để cải thiện Context Precision.",
        "3. Tăng ràng buộc trích dẫn trong prompt sinh câu trả lời khi Faithfulness thấp.",
        "",
        f"> Chi tiết từng câu được lưu tại `{RAW_RESULTS_PATH.name}`.",
    ])
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} golden records")
    llm = build_llm()
    eval_data = generate_evaluation_data(golden_dataset, llm)
    result = evaluate_with_ragas(eval_data, llm)
    export_results(result.to_pandas())
    print(f"Saved report: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
