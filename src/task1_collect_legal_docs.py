"""
Task 1 — Thu thập văn bản chính sách/quy định dịch vụ đại học.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang công khai của một trường đại học.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.

Gợi ý nguồn (ví dụ trang công khai RMIT Vietnam — rmit.edu.vn):
    - https://www.rmit.edu.vn/study-at-rmit/tuition-fees
    - https://www.rmit.edu.vn/study-at-rmit/scholarships/...
    - https://www.rmit.edu.vn/students/my-studies/fees-and-payments

Gợi ý văn bản (chủ đề dịch vụ đại học):
    - Học phí & phương thức thanh toán (Tuition Fees)
    - Chính sách học bổng (Scholarship eligibility)
    - Quy định ký túc xá / hỗ trợ chỗ ở (Accommodation Services)
    - Hướng dẫn đăng ký học phần qua cổng thông tin sinh viên (Course Registration)

Lưu ý: một số trang trường (vd VinUni, Fulbright) chặn bot crawler mặc định (HTTP 403) —
không phải lỗi của bạn, đó là cấu hình WAF/Cloudflare phía server. Đổi sang trang khác
thay vì cố vượt qua, và chỉ dùng nguồn công khai/được phép chia sẻ.
"""

from pathlib import Path
from urllib.request import Request, urlopen

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

LEGAL_DOCUMENTS = {
    "hust-undergraduate-training-regulation-2024.pdf": "https://sdh.hust.edu.vn/Upload/19/files/Quyche/2024/10_2%20Quy%20ch%E1%BA%BF%20TCQL%20%C4%90%C3%A0o%20t%E1%BA%A1o_2024_VP%C4%90H_final_%C4%91%C3%A3%20k%C3%BD.pdf",
    "hust-phd-scholarship-regulation-2026.pdf": "https://sdh.hust.edu.vn/Upload/19/Files/Quyche/2026/Quyet_dinh_hoc_bong_NCS.pdf",
    "hust-credit-based-training-regulation.pdf": "https://www.hust.edu.vn/uploads/sys/quality-assurance/2019/04/ee-1-2-3-moet-regulation-on-the-credit-based-training-program.399978.17779.pdf",
    "hust-training-regulation-2025.pdf": "https://sdh.hust.edu.vn/Upload/19/files/Quyche/2025/01_%20Quy%20ch%E1%BA%BF%20%C4%91%C3%A0o%20t%E1%BA%A1o%202025_5445_Q%C4%90-%C4%90HBK_%C4%91%C3%A3%20k%C3%BD.pdf",
    "hust-academic-integrity-regulation-2025.pdf": "https://sdh.hust.edu.vn/Upload/19/files/Quyche/2025/QD%20ban%20hanh%20LCHT2025.pdf",
}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_file(url: str, filename: str) -> Path:
    """Download one public source document with basic validation."""
    setup_directory()
    destination = DATA_DIR / filename
    request = Request(url, headers={"User-Agent": "VinUni-Day08-RAG/1.0"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    if len(content) <= 1024:
        raise ValueError(f"Downloaded file is unexpectedly small: {url}")
    destination.write_bytes(content)
    print(f"Downloaded: {destination}")
    return destination


def download_all() -> list[Path]:
    return [download_file(url, filename) for filename, url in LEGAL_DOCUMENTS.items()]


# TODO: Tải file PDF/DOCX về DATA_DIR
# Có thể tải thủ công hoặc viết script download nếu có direct link.
#
# Ví dụ nếu có direct link:
#
# import requests
#
# def download_file(url: str, filename: str):
#     response = requests.get(url)
#     filepath = DATA_DIR / filename
#     filepath.write_bytes(response.content)
#     print(f"✓ Đã tải: {filepath}")
#
# Nếu trang là HTML thuần (không phải PDF sẵn), có thể convert nội dung text
# thành PDF đơn giản bằng thư viện fpdf2 (đã có trong requirements.txt).


if __name__ == "__main__":
    download_all()
