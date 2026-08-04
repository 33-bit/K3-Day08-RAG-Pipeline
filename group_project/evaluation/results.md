# RAG Evaluation Results

Framework used: **RAGAS**

## Overall Scores

| Metric | hybrid_rerank | dense_only | Δ |
|--------|--------:|--------:|--------:|
| Faithfulness | 0.677 | 0.645 | 0.032 |
| Answer Relevancy | 0.437 | 0.313 | 0.124 |
| Context Recall | 0.903 | 0.731 | 0.173 |
| Context Precision | 0.139 | 0.099 | 0.041 |
| **Average** | **0.539** | **0.447** | **0.092** |

## A/B Comparison Analysis

**Config A (hybrid_rerank):** Hybrid search + reranking
**Config B (dense_only):** Dense-only retrieval without reranking

**Kết luận:** hybrid_rerank đang nhỉnh hơn về trung bình tổng thể, chủ yếu nhờ giữ chất lượng context tốt hơn sau reranking.

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------:|----------:|-------:|---------------|------------|
| 1 | Sinh viên được đăng ký học chương trình thứ hai sớm nhất khi nào? | 0.500 | 0.333 | 0.640 | Noisy context | Top-k contains many unrelated chunks, so precision drops. |
| 2 | Sinh viên cử nhân hoặc kỹ sư rút học phần trong 7 tuần đầu học kỳ phải đóng bao nhiêu học phí? | 0.467 | 0.235 | 0.909 | Noisy context | Top-k contains many unrelated chunks, so precision drops. |
| 3 | Nghiên cứu sinh cần có thành tích công bố khoa học nào để đăng ký bảo vệ luận án cấp cơ sở? | 0.556 | 0.250 | 0.800 | Noisy context | Top-k contains many unrelated chunks, so precision drops. |

## Recommendations

### Cải tiến 1
**Action:** Tăng chất lượng retrieval bằng tuning `top_k`, `score_threshold`, và query expansion cho các câu hỏi dài.
**Expected impact:** Nâng context recall từ 0.903 lên mức ổn định hơn.


### Cải tiến 2
**Action:** Giảm noise bằng cách giữ reranking cho nhóm câu hỏi cần evidence rõ ràng và giảm `top_k` nếu precision thấp.
**Expected impact:** Cải thiện context precision từ 0.139 và giảm câu trả lời lệch nguồn.

### Cải tiến 3
**Action:** Siết prompt generation để answer luôn bám citation và từ chối khi evidence không đủ.
**Expected impact:** Tăng faithfulness từ 0.677 và giảm hallucination.
