"""CP4 Role 2 audit for the standardized RAG corpus."""

from collections import Counter
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parents[1] / "data" / "standardized"


def audit_corpus() -> dict:
    files = sorted(STANDARDIZED_DIR.rglob("*.md"))
    records = []
    errors = []
    for path in files:
        relative = path.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = relative.split("/", 1)[0].lower()
        if doc_type not in {"legal", "news"}:
            errors.append(f"{relative}: invalid doc_type={doc_type}")
        if path.stat().st_size <= 200:
            errors.append(f"{relative}: file is too small")
        records.append({"source": relative, "doc_type": doc_type, "bytes": path.stat().st_size})

    counts = Counter(record["doc_type"] for record in records)
    if counts["legal"] < 5:
        errors.append(f"expected at least 5 legal files, found {counts['legal']}")
    if counts["news"] < 5:
        errors.append(f"expected at least 5 news files, found {counts['news']}")
    return {"files": records, "counts": dict(counts), "errors": errors}


if __name__ == "__main__":
    report = audit_corpus()
    print(f"files={len(report['files'])} counts={report['counts']}")
    if report["errors"]:
        for error in report["errors"]:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("CP4 Role 2 corpus audit: PASS")
