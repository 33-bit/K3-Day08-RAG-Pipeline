"""UniHelp — a student-focused Streamlit interface for the RAG pipeline."""

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Page configuration
st.set_page_config(
    page_title="UniHelp AI | HUST Student Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS & Premium Design System
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      
      html, body, [class*="css"] {
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      }
      
      .stApp {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          color: #f8fafc;
      }
      
      .block-container {
          max-width: 1100px;
          padding-top: 1.8rem;
          padding-bottom: 6rem;
      }
      
      /* Sidebar styling */
      [data-testid="stSidebar"] {
          background: rgba(15, 23, 42, 0.85);
          backdrop-filter: blur(12px);
          border-right: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      [data-testid="stSidebar"] * {
          color: #e2e8f0 !important;
      }

      /* Hero Header Banner */
      .hero-banner {
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 16px;
          padding: 1.5rem 1.8rem;
          margin-bottom: 2rem;
          box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
      }

      .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          border-radius: 999px;
          background: rgba(16, 185, 129, 0.2);
          border: 1px solid rgba(16, 185, 129, 0.4);
          color: #34d399 !important;
          font-size: 0.82rem;
          font-weight: 600;
          margin-bottom: 0.8rem;
      }

      .brand-title {
          font-size: 2.2rem;
          font-weight: 800;
          background: linear-gradient(135deg, #34d399 0%, #38bdf8 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
          line-height: 1.2;
      }

      .brand-subtitle {
          color: #94a3b8;
          font-size: 1.05rem;
          margin-top: 0.4rem;
          margin-bottom: 0;
      }

      /* Quick Suggestion Chips */
      .quick-chip-btn {
          background: rgba(30, 41, 59, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 1rem;
          color: #f1f5f9;
          font-size: 0.95rem;
          transition: all 0.3s ease;
          cursor: pointer;
      }

      .quick-chip-btn:hover {
          border-color: #34d399;
          transform: translateY(-2px);
          box-shadow: 0 8px 20px -6px rgba(52, 211, 153, 0.3);
      }

      /* Metric Cards */
      .metric-card {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 0.9rem;
          text-align: center;
      }

      .metric-val {
          font-size: 1.4rem;
          font-weight: 700;
          color: #38bdf8;
      }

      .metric-lbl {
          font-size: 0.78rem;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
      }

      /* Source Drawer Card */
      .source-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          padding: 1rem;
          margin-bottom: 0.75rem;
      }

      .source-badge-legal {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
          border: 1px solid rgba(16, 185, 129, 0.3);
          padding: 2px 8px;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
      }

      .source-badge-news {
          background: rgba(56, 189, 248, 0.2);
          color: #38bdf8;
          border: 1px solid rgba(56, 189, 248, 0.3);
          padding: 2px 8px;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
      }

      .source-badge-pageindex {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
          border: 1px solid rgba(245, 158, 11, 0.3);
          padding: 2px 8px;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
      }

      .source-content {
          color: #cbd5e1;
          font-size: 0.88rem;
          line-height: 1.5;
          margin-top: 0.5rem;
          background: rgba(15, 23, 42, 0.4);
          padding: 0.6rem 0.8rem;
          border-radius: 8px;
          border-left: 3px solid #38bdf8;
      }
      
      /* Badges */
      .badge-hybrid {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
          border: 1px solid rgba(16, 185, 129, 0.3);
          padding: 3px 10px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
      }

      .badge-pageindex {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
          border: 1px solid rgba(245, 158, 11, 0.3);
          padding: 3px 10px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
      }

      .badge-speed {
          background: rgba(56, 189, 248, 0.2);
          color: #38bdf8;
          border: 1px solid rgba(56, 189, 248, 0.3);
          padding: 3px 10px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


SUGGESTIONS = [
    {"icon": "💰", "label": "Chính sách học phí ĐHBK Hà Nội"},
    {"icon": "🏆", "label": "Điều kiện học bổng nghiên cứu sinh"},
    {"icon": "📖", "label": "Quy chế đào tạo đại học chính quy"},
    {"icon": "🏫", "label": "Thông điệp của Giám đốc Đại học Bách khoa"},
]


def render_source_panel(sources: list[dict]) -> None:
    """Render expandable rich drawer for reference documents."""
    if not sources:
        return

    with st.expander(f"📚 Nguồn tài liệu trích dẫn ({len(sources)} kết quả)"):
        for index, src in enumerate(sources, start=1):
            metadata = src.get("metadata", {})
            source_file = metadata.get("source") or metadata.get("file_name") or f"Document-{index}"
            doc_type = (metadata.get("doc_type") or metadata.get("type") or "legal").upper()
            score = src.get("score", 0.0)
            origin = src.get("source", "hybrid")
            excerpt = src.get("content", "Không có nội dung.")

            badge_style = "source-badge-legal" if "LEGAL" in doc_type else "source-badge-news"
            if origin == "pageindex":
                badge_style = "source-badge-pageindex"

            st.markdown(
                f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <div>
                            <span class="{badge_style}">{doc_type}</span>
                            <strong style="margin-left: 8px; font-size: 0.95rem; color: #f1f5f9;">{index}. {source_file}</strong>
                        </div>
                        <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 600;">
                            Score: {score:.4f}
                        </div>
                    </div>
                    <div class="source-content">
                        {excerpt[:350]}{'...' if len(excerpt) > 350 else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# Sidebar Controls & Metrics
with st.sidebar:
    st.markdown("### 🎓 UniHelp RAG Engine")
    st.caption("v2.0.0 · Role 3 - Vector Search Dev")

    if st.button("＋ Tạo cuộc trò chuyện mới", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

    st.divider()
    st.markdown("⚙️ **Cấu Hình Pipeline**")
    top_k = st.slider("Số lượng tài liệu (Top-K)", min_value=1, max_value=10, value=5)
    score_threshold = st.slider("Ngưỡng Fallback (Cosine)", min_value=0.1, max_value=0.8, value=0.48, step=0.02)
    use_reranking = st.toggle("Kích hoạt RRF Reranking ($k=60$)", value=True)

    st.divider()
    st.markdown("📊 **Thông Số Hệ Thống**")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-val">607</div>
                <div class="metric-lbl">Vector Chunks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-val">384d</div>
                <div class="metric-lbl">Embedding Dim</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("ChromaDB persistent store · all-MiniLM-L6-v2 · BM25 Okapi · PageIndex Vectorless Fallback")


# Main Interface Tabs
tab_chat, tab_metrics, tab_guide = st.tabs(["💬 Trợ Lý UniHelp", "📊 Pipeline Debugger", "📖 Hướng Dẫn & Cấu Trúc"])

with tab_chat:
    # Hero Banner Header
    st.markdown(
        """
        <div class="hero-banner">
            <div class="status-pill">
                <span>🟢</span> Engine Online · ChromaDB & RRF Active
            </div>
            <h1 class="brand-title">UniHelp AI Engine</h1>
            <p class="brand-subtitle">Trợ lý tra cứu chính sách, quy chế đào tạo, học phí & học bổng Đại học Bách khoa Hà Nội</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggestion Chips if no messages yet
    if not st.session_state.messages:
        st.markdown("<p style='color: #94a3b8; font-weight: 600; margin-bottom: 0.8rem;'>💡 Gợi ý câu hỏi phổ biến:</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for idx, sug in enumerate(SUGGESTIONS):
            col = col1 if idx % 2 == 0 else col2
            if col.button(f"{sug['icon']} {sug['label']}", use_container_width=True, key=f"sug_{idx}"):
                st.session_state.pending_query = sug["label"]

    # Render History Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            text = msg.get("content") or msg.get("answer", "")
            st.markdown(text)
            if msg["role"] == "assistant":
                origin = msg.get("retrieval_source", "none")
                badge_class = "badge-pageindex" if origin == "pageindex" else "badge-hybrid"
                badge_text = "PageIndex Fallback" if origin == "pageindex" else "Hybrid Retrieval (RRF)"
                elapsed = msg.get("elapsed_time", 0.0)

                badges_html = f'<span class="{badge_class}">{badge_text}</span> '
                if elapsed > 0:
                    badges_html += f'<span class="badge-speed">⚡ Tốc độ: {elapsed:.3f}s</span>'

                st.markdown(f"<div style='margin-top: 0.6rem;'>{badges_html}</div>", unsafe_allow_html=True)
                render_source_panel(msg.get("sources", []))

    # User Input Query
    user_input = st.chat_input("Nhập câu hỏi tra cứu quy chế, học phí, học bổng Bách khoa…")
    query = user_input or st.session_state.pending_query

    if query:
        st.session_state.pending_query = None
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("UniHelp đang thực thi Retrieval Pipeline (Task 9)…"):
                start_time = time.perf_counter()
                try:
                    from src.task9_retrieval_pipeline import retrieve
                    sources = retrieve(
                        query=query,
                        top_k=top_k,
                        score_threshold=score_threshold,
                        use_reranking=use_reranking,
                    )
                    elapsed_time = time.perf_counter() - start_time
                    retrieval_source = sources[0].get("source", "hybrid") if sources else "none"

                    # Check LLM Generation Task 10
                    try:
                        from src.task10_generation import generate_with_citation
                        gen_res = generate_with_citation(query, top_k=top_k)
                        answer = gen_res.get("answer", "")
                    except (NotImplementedError, Exception):
                        if sources:
                            doc_names = list(dict.fromkeys(s.get("metadata", {}).get("source", "Tài liệu") for s in sources))
                            answer = f"### 📍 Kết quả truy vấn từ RAG Pipeline (Task 9)\n\n"
                            answer += f"**Nguồn tài liệu tìm thấy ({len(sources)} chunks):** `{', '.join(doc_names)}`\n\n"
                            answer += f"#### Trích đoạn nội dung ưu tiên cao nhất:\n"
                            answer += f"> {sources[0]['content']}"
                        else:
                            answer = "⚠️ **Thông báo:** Không tìm thấy tài liệu phù hợp trong cơ sở dữ liệu."

                    response = {
                        "content": answer,
                        "answer": answer,
                        "sources": sources,
                        "retrieval_source": retrieval_source,
                        "elapsed_time": elapsed_time,
                    }
                except Exception as error:
                    response = {
                        "content": f"⚠️ Không thể kết nối pipeline lúc này: {error}",
                        "answer": f"⚠️ Không thể kết nối pipeline lúc này: {error}",
                        "sources": [],
                        "retrieval_source": "none",
                        "elapsed_time": 0.0,
                    }


            st.markdown(response["answer"])
            origin = response["retrieval_source"]
            badge_class = "badge-pageindex" if origin == "pageindex" else "badge-hybrid"
            badge_text = "PageIndex Fallback" if origin == "pageindex" else "Hybrid Retrieval (RRF)"
            elapsed = response.get("elapsed_time", 0.0)

            badges_html = f'<span class="{badge_class}">{badge_text}</span> '
            if elapsed > 0:
                badges_html += f'<span class="badge-speed">⚡ Tốc độ: {elapsed:.3f}s</span>'

            st.markdown(f"<div style='margin-top: 0.6rem;'>{badges_html}</div>", unsafe_allow_html=True)
            render_source_panel(response["sources"])

        st.session_state.messages.append({"role": "assistant", **response})


with tab_metrics:
    st.markdown("### 📊 Retrieval Pipeline Debugger & Comparison")
    st.caption("So sánh độc lập kết quả giữa Semantic Search (Dense) và Lexical Search (Sparse BM25)")

    debug_query = st.text_input("Nhập câu hỏi chạy thử nghiệm kiểm tra:", value="Quy định học bổng đối với nghiên cứu sinh")
    if st.button("🚀 Chạy phân tích so sánh", type="primary"):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### 🟢 Semantic Search (Dense Vector)")
            try:
                from src.task5_semantic_search import semantic_search
                sem_res = semantic_search(debug_query, top_k=3)
                if sem_res:
                    st.success(f"Best Cosine Score: {sem_res[0]['score']:.4f}")
                    for r in sem_res:
                        st.markdown(f"**[{r['score']:.4f}]** `{r.get('metadata',{}).get('source','')}`")
                        st.caption(f"{r['content'][:180]}...")
                else:
                    st.warning("Không có kết quả")
            except Exception as e:
                st.error(f"Lỗi Semantic Search: {e}")

        with c2:
            st.markdown("#### 🔵 Lexical Search (Sparse BM25)")
            try:
                from src.task6_lexical_search import lexical_search
                lex_res = lexical_search(debug_query, top_k=3)
                if lex_res:
                    st.info(f"Best BM25 Score: {lex_res[0]['score']:.4f}")
                    for r in lex_res:
                        st.markdown(f"**[{r['score']:.4f}]** `{r.get('metadata',{}).get('source','')}`")
                        st.caption(f"{r['content'][:180]}...")
                else:
                    st.warning("Không có kết quả")
            except Exception as e:
                st.error(f"Lỗi Lexical Search: {e}")


with tab_guide:
    st.markdown("### 📖 Kiến Trúc & Cấu Hình Kỹ Thuật (Role 3)")
    st.markdown(
        """
        - **Chunking Strategy:** `RecursiveCharacterTextSplitter` (`CHUNK_SIZE=500`, `CHUNK_OVERLAP=50`).
        - **Vector Database:** `ChromaDB` local persistent store (`chroma_db/`, 607 chunks).
        - **Embedding Model:** `all-MiniLM-L6-v2` (384 dimensions).
        - **Sparse Search:** `BM25Okapi` ($k_1=1.5, b=0.75$).
        - **Rank Fusion:** Reciprocal Rank Fusion ($k=60$) kết hợp Reranker API Fallback.
        - **Safety Trigger:** PageIndex Vectorless Fallback khi Cosine Score gốc $< 0.48$.
        """
    )
