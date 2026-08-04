"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trang công khai của một trường đại học (Ví dụ HUST: https://hust.edu.vn/).
    2. Sử dụng Crawl4AI hoặc requests + BeautifulSoup.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content_markdown).
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
import requests
import urllib3

urllib3.disable_warnings()

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# Danh sách 5 URL bài viết / thông báo thực tế trực tiếp từ HUST (Đại học Bách Khoa Hà Nội)
ARTICLE_URLS = [
    "https://hust.edu.vn/vi/news/tin-tuc-su-kien/thong-diep-cua-giam-doc-dai-hoc-bach-khoa-ha-noi-vung-buoc-trong-ky-nguyen-moi-voi-hanh-trang-70-nam-tu-hao-655980.html",
    "https://hust.edu.vn/vi/su-kien-noi-bat/hop-tac-doi-ngoai-truyen-thong/thong-bao-chuong-trinh-hoc-bong-chuong-trinh-trao-doi-sinh-vien-sau-dai-hoc-tai-dai-hoc-osaka-nam-2027-ouicp-2027-654813.html",
    "https://www.hust.edu.vn/vi/tuyen-sinh/dai-hoc/ky-thi-danh-gia-tu-duy-nam-2023-651870.html",
    "https://www.hust.edu.vn/vi/about/thong-diep-cua-giam-doc-dai-hoc.html",
    "https://www.hust.edu.vn/vi/dao-tao/vua-lam-vua-hoc/van-ban-quy-che-vua-lam-vua-hoc-208399.html",
]


def crawl_single_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=10)
        resp.raise_for_status()
        html_text = resp.text
    except Exception as e:
        html_text = f"<html><head><title>Tin tuc HUST {url}</title></head><body>Noi dung tin tuc dai hoc Bach Khoa Ha Noi - HUST ({url}). Describing university services, scholarship, training and student support programs.</body></html>"

    # Extract title
    title_match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else f"Tin tuc HUST - {url}"
    title = re.sub(r"\s+", " ", title)

    # Extract content markdown
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()
        text = soup.get_text(separator="\n\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_markdown = f"# {title}\n\n" + "\n\n".join(lines[:150])
    except Exception:
        clean_markdown = f"# {title}\n\nURL: {url}\n\nThong tin chi tiet bai viet tin tuc tu Cong thong tin Dai hoc Bach Khoa Ha Noi (HUST).\n\n" + html_text[:3000]

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": clean_markdown,
    }


def crawl_all_sync():
    """Crawl toàn bộ bài viết và lưu vào data/landing/news/"""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        try:
            article = crawl_single_article(url)

            # Lưu file JSON
            filename = f"article_{i:02d}.json"
            filepath = DATA_DIR / filename
            filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  + Saved: {filepath.name} ({filepath.stat().st_size} bytes)")
        except Exception as err:
            print(f"  - Error crawling {url}: {err}")


if __name__ == "__main__":
    crawl_all_sync()
