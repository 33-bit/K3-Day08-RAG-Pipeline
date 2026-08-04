from statistics import mean, median
from time import perf_counter

from src.task7_reranking import rerank_rrf
from src.task8_pageindex_vectorless import DOC_IDS_PATH, pageindex_search


QUERY = "Đạo văn và tự đạo văn được hiểu như thế nào?"
TOP_K = 5


# Dữ liệu giả lập kết quả từ Semantic Search và BM25.
# Không gọi embedding/BM25 vì mục tiêu là đo riêng RRF.
dense_results = [
    {
        "content": f"Nội dung tài liệu {i}",
        "score": 0.9 - i * 0.01,
        "metadata": {"source": "dense"},
    }
    for i in range(100)
]

sparse_results = [
    {
        "content": f"Nội dung tài liệu {i}",
        "score": 20.0 - i * 0.1,
        "metadata": {"source": "bm25"},
    }
    for i in reversed(range(100))
]


def benchmark_rrf(repeats=1000):
    durations = []

    for _ in range(repeats):
        start = perf_counter()
        rerank_rrf(
            [dense_results, sparse_results],
            top_k=TOP_K,
        )
        durations.append((perf_counter() - start) * 1000)

    return durations


def benchmark_pageindex(repeats=3):
    if not DOC_IDS_PATH.exists():
        raise RuntimeError(
            f"Thiếu {DOC_IDS_PATH}. Hãy upload tài liệu và lưu doc_id trước khi đo."
        )

    durations = []

    for attempt in range(1, repeats + 1):
        try:
            start = perf_counter()
            results = pageindex_search(QUERY, top_k=TOP_K)
            elapsed_ms = (perf_counter() - start) * 1000
        except Exception as exc:
            message = str(exc)
            print(f"PageIndex lần {attempt}: không thực hiện được ({message})")
            if "credit" in message.lower():
                print("Dừng benchmark PageIndex vì tài khoản đã hết credit.")
                break
            raise

        durations.append(elapsed_ms)
        print(
            f"PageIndex lần {attempt}: "
            f"{elapsed_ms:.2f} ms, {len(results)} kết quả"
        )

    return durations


def print_summary(name, durations):
    if not durations:
        print(f"\n{name}")
        print("  Không có lần đo thành công.")
        return

    print(f"\n{name}")
    print(f"  Số lần đo : {len(durations)}")
    print(f"  Trung bình: {mean(durations):.2f} ms")
    print(f"  Trung vị  : {median(durations):.2f} ms")
    print(f"  Thấp nhất : {min(durations):.2f} ms")
    print(f"  Cao nhất  : {max(durations):.2f} ms")


if __name__ == "__main__":
    rrf_times = benchmark_rrf()
    print_summary("RRF latency", rrf_times)

    pageindex_times = benchmark_pageindex()
    print_summary("PageIndex latency", pageindex_times)
