"""UniHelp — a student-focused Streamlit interface for the RAG pipeline."""

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.ui_helpers import (
    format_score,
    normalise_source_metadata,
    resolve_response,
)

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="UniHelp | Dịch vụ sinh viên",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #f7fbf9; }
      .block-container { max-width: 980px; padding-top: 2rem; padding-bottom: 7rem; }
      [data-testid="stSidebar"] { background: #063f36; }
      [data-testid="stSidebar"] * { color: #f0fdf4; }
      [data-testid="stSidebar"] .stSlider p { color: #d1fae5; }
      .uni-brand { color: #065f46; font-size: 2.2rem; font-weight: 750; margin-bottom: 0; }
      .uni-subtitle { color: #52716b; margin-top: 0.3rem; }
      .status-badge { display: inline-block; margin: 0.6rem 0 0.2rem; padding: 0.2rem 0.55rem; border-radius: 999px; background: #d1fae5; color: #065f46; font-size: 0.78rem; font-weight: 650; }
      .source-card { padding: 0.7rem 0; border-bottom: 1px solid #d1fae5; }
      .source-card:last-child { border-bottom: 0; }
      .source-meta { color: #52716b; font-size: 0.82rem; }
      .quick-label { color: #52716b; font-size: 0.92rem; margin: 1.5rem 0 0.35rem; }
      .demo-note { color: #9a6700; background: #fff8c5; border-radius: 0.6rem; padding: 0.65rem 0.8rem; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


SUGGESTIONS = [
    "Học phí tại RMIT Vietnam là bao nhiêu?",
    "Làm sao để đặt phòng học nhóm ở thư viện?",
    "Điều kiện xin học bổng Academic Achievement?",
    "Dịch vụ hỗ trợ chỗ ở cho sinh viên như thế nào?",
]


def source_panel(sources: list[dict]) -> None:
    """Render the shared expandable source drawer for an assistant answer."""
    if not sources:
        return

    with st.expander(f"📚 Nguồn tham khảo ({len(sources)})"):
        for index, source in enumerate(sources, start=1):
            metadata = normalise_source_metadata(source.get("metadata", {}), f"document-{index}")
            name = metadata.get("source", f"Tài liệu {index}")
            document_type = metadata.get("doc_type", "tài liệu")
            score = source.get("score")
            score_text = f" · score {format_score(score)}" if isinstance(score, (int, float)) else ""
            excerpt = source.get("content", "Không có đoạn trích.")
            st.markdown(
                f"<div class='source-card'><strong>{index}. {name}</strong>"
                f"<div class='source-meta'>{document_type}{score_text}</div>"
                f"<div>{excerpt[:300]}{'...' if len(excerpt) > 300 else ''}</div></div>",
                unsafe_allow_html=True,
            )


if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

with st.sidebar:
    st.markdown("## 🎓 UniHelp")
    st.caption("Trợ lý dịch vụ sinh viên")
    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

    st.divider()
    st.markdown("**Khám phá nhanh**")
    for suggestion in SUGGESTIONS:
        if st.button(suggestion, use_container_width=True, key=f"side_{suggestion}"):
            st.session_state.pending_query = suggestion

    st.divider()
    st.markdown("**Thiết lập**")
    top_k = st.slider("Số nguồn tham khảo", min_value=3, max_value=10, value=5)
    st.caption("Hybrid Retrieval · RRF · PageIndex fallback")

st.markdown("<p class='uni-brand'>Chào bạn, mình là UniHelp 👋</p>", unsafe_allow_html=True)
st.markdown(
    "<p class='uni-subtitle'>Hỏi nhanh về học phí, học bổng, thư viện, chỗ ở và đăng ký học phần.</p>",
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown("<p class='quick-label'>Bạn muốn tìm thông tin gì?</p>", unsafe_allow_html=True)
    suggestion_columns = st.columns(2)
    for index, suggestion in enumerate(SUGGESTIONS):
        if suggestion_columns[index % 2].button(suggestion, use_container_width=True, key=f"main_{suggestion}"):
            st.session_state.pending_query = suggestion

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            origin = message.get("retrieval_source", "none")
            label = {"hybrid": "Hybrid Retrieval", "pageindex": "PageIndex", "none": "Đang chờ pipeline"}.get(origin, origin)
            st.markdown(f"<span class='status-badge'>{label}</span>", unsafe_allow_html=True)
            source_panel(message.get("sources", []))

user_input = st.chat_input("Nhập câu hỏi về dịch vụ hoặc chính sách đại học…")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("UniHelp đang tìm tài liệu phù hợp…"):
            try:
                from src.task10_generation import generate_with_citation

                response, is_demo = resolve_response(query, top_k, generate_with_citation)
            except Exception as error:
                response = {
                    "answer": f"⚠️ Không thể kết nối pipeline lúc này: {error}",
                    "sources": [],
                    "retrieval_source": "none",
                }
                is_demo = False

        st.markdown(response["answer"])
        if is_demo:
            st.markdown(
                "<div class='demo-note'>Đang hiển thị dữ liệu minh hoạ vì Task 10 chưa hoàn thiện.</div>",
                unsafe_allow_html=True,
            )
        origin = response["retrieval_source"]
        label = {"hybrid": "Hybrid Retrieval", "pageindex": "PageIndex", "none": "Đang chờ pipeline"}.get(origin, origin)
        st.markdown(f"<span class='status-badge'>{label}</span>", unsafe_allow_html=True)
        source_panel(response["sources"])

    st.session_state.messages.append({"role": "assistant", **response})
