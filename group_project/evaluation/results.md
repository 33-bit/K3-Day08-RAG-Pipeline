# RAGAS Evaluation Results

## Run Information

- Evaluated at: 2026-08-04T15:13:22+07:00
- Framework: RAGAS 0.1.21
- Judge model: `openai/gpt-4o-mini` via OpenRouter
- Dataset: 20 golden Q&A records
- Retrieval: BM25, top_k=5

## Overall Scores

| Metric | Score |
|---|---:|
| Faithfulness | 0.8667 |
| Answer Relevance | 0.1045 |
| Context Recall | 0.8833 |
| Context Precision | 0.9790 |
| **Average** | **0.7084** |

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Precision |
|---:|---|---:|---:|---:|---:|
| 1 | Theo Quy chế đào tạo năm 2025 của Đại học Bách khoa Hà Nội, chương trình cử nhân chính quy có thời gian và khối lượng học tập chuẩn tối thiểu là bao nhiêu? | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 2 | Học viên thạc sĩ chính quy và vừa làm vừa học được đăng ký tối đa bao nhiêu tín chỉ? | 0.6667 | 0.0000 | 0.5000 | 1.0000 |
| 3 | Học phần tiên quyết, học phần học trước và học phần song hành khác nhau như thế nào? | 0.3333 | 0.1291 | 1.0000 | 1.0000 |

## Recommendations

1. Điều chỉnh tokenizer BM25 cho tiếng Việt và tăng kích thước đoạn khi Context Recall thấp.
2. Dùng hybrid dense + BM25 và reranking để cải thiện Context Precision.
3. Tăng ràng buộc trích dẫn trong prompt sinh câu trả lời khi Faithfulness thấp.

> Chi tiết từng câu được lưu tại `ragas_results.json`.
