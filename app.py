"""UniHelp — a student-focused Streamlit interface for the RAG pipeline."""

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.ui_helpers import format_score, normalise_source_metadata, resolve_response

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

      :root {
          --canvas: #0B1220;
          --surface: #111C2E;
          --surface-raised: #18263B;
          --border: #2A3B55;
          --text-primary: #F1F5F9;
          --text-secondary: #B6C4D6;
          --teal: #2DD4BF;
          --teal-deep: #0F766E;
          --amber: #FBBF24;
          --danger: #FB7185;
      }

      html, body, [class*="css"] {
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      }

      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"] {
          background: var(--canvas);
          color: var(--text-primary);
      }

      [data-testid="stHeader"] {
          background: var(--canvas) !important;
          border-bottom: 1px solid var(--border);
      }

      [data-testid="stToolbar"],
      [data-testid="stDecoration"] {
          background: transparent !important;
      }

      .block-container {
          max-width: 1100px;
          padding-top: 1.8rem;
          padding-bottom: 6rem;
      }

      [data-testid="stSidebar"] {
          background: #0D1628;
          border-right: 1px solid var(--border);
      }

      [data-testid="stSidebar"] :is(p, label, h1, h2, h3, span) {
          color: var(--text-secondary);
      }

      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] strong {
          color: var(--text-primary);
      }

      [data-testid="stTabs"] [role="tab"] {
          color: var(--text-secondary);
          font-weight: 700;
      }

      [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
          color: var(--teal);
      }

      [data-testid="stTabs"] [role="tab"]:focus-visible,
      [data-testid="stButton"] > button:focus-visible,
      [data-testid="stChatInput"] textarea:focus-visible {
          outline: 2px solid var(--teal) !important;
          outline-offset: 2px;
      }

      [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
          background-color: var(--teal);
      }

      [data-testid="stButton"] > button {
          min-height: 2.9rem;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 10px;
          color: var(--text-primary) !important;
          font-weight: 600;
          transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
      }

      [data-testid="stButton"] > button:hover {
          background: var(--surface-raised);
          border-color: var(--teal);
          color: var(--text-primary) !important;
          transform: translateY(-1px);
      }

      [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {
          background: var(--danger);
          border-color: var(--danger);
          color: #FFFFFF !important;
      }

      [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover {
          background: #E11D48;
          border-color: #E11D48;
      }

      .hero-banner {
          background: linear-gradient(135deg, #123B43 0%, #142D48 100%);
          border: 1px solid rgba(45, 212, 191, 0.48);
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
          border: 1px solid rgba(45, 212, 191, 0.55);
          border-radius: 999px;
          background: rgba(45, 212, 191, 0.14);
          color: var(--teal) !important;
          font-size: 0.82rem;
          font-weight: 700;
          margin-bottom: 0.8rem;
      }

      .brand-title {
          margin: 0;
          background: linear-gradient(135deg, #5EEAD4 0%, #67E8F9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          font-size: 2.2rem;
          font-weight: 800;
          line-height: 1.2;
      }

      .brand-subtitle {
          color: var(--text-secondary);
          font-size: 1.05rem;
          margin: 0.4rem 0 0;
      }

      [data-testid="stChatInput"] {
          background: var(--surface-raised);
          border: 1px solid var(--border);
          border-radius: 14px;
      }

      [data-testid="stChatInput"] > div {
          background: var(--surface-raised) !important;
          border-radius: 14px;
      }

      [data-testid="stChatInput"]:focus-within {
          border-color: var(--teal);
          box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.16);
      }

      [data-testid="stChatInput"] textarea {
          color: var(--text-primary) !important;
      }

      [data-testid="stChatInput"] textarea::placeholder {
          color: var(--text-secondary) !important;
          opacity: 0.9;
      }

      [data-testid="stChatInput"] button {
          background: var(--teal);
          color: #06201F !important;
      }

      [data-testid="stChatMessage"] {
          margin: 0.65rem 0;
          padding: 0.8rem 1rem;
          border: 1px solid var(--border);
          border-radius: 14px;
          background: var(--surface-raised);
      }

      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
          background: var(--teal-deep);
          border-color: #159A8A;
      }

      [data-testid="stChatMessage"] :is(p, li, h1, h2, h3, h4, blockquote, strong) {
          color: var(--text-primary) !important;
      }

      [data-testid="stChatMessage"] a,
      [data-testid="stExpander"] a {
          color: var(--teal) !important;
          text-decoration: underline;
          text-underline-offset: 2px;
      }

      [data-testid="stChatMessage"] code {
          background: #0A1424;
          border: 1px solid var(--border);
          border-radius: 4px;
          color: #BAE6FD;
          padding: 0.1rem 0.3rem;
      }

      [data-testid="stExpander"] {
          border: 1px solid var(--border);
          border-radius: 10px;
          background: var(--surface);
      }

      [data-testid="stExpander"] summary,
      [data-testid="stExpander"] summary span,
      [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
          color: var(--text-primary) !important;
      }

      [data-testid="stExpander"] details > div {
          background: var(--surface);
      }

      .metric-card,
      .source-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 12px;
      }

      .metric-card {
          padding: 0.9rem;
          text-align: center;
      }

      .metric-val {
          color: #67E8F9;
          font-size: 1.4rem;
          font-weight: 700;
      }

      .metric-lbl {
          color: var(--text-secondary);
          font-size: 0.78rem;
          letter-spacing: 0.5px;
          text-transform: uppercase;
      }

      .source-card {
          margin-bottom: 0.75rem;
          padding: 1rem;
      }

      .source-content {
          margin-top: 0.5rem;
          padding: 0.6rem 0.8rem;
          border-left: 3px solid #67E8F9;
          border-radius: 8px;
          background: #0A1424;
          color: var(--text-secondary);
          font-size: 0.88rem;
          line-height: 1.5;
      }

      .source-badge-legal,
      .badge-hybrid {
          background: rgba(45, 212, 191, 0.14);
          border: 1px solid rgba(45, 212, 191, 0.38);
          color: var(--teal);
      }

      .source-badge-news,
      .badge-speed {
          background: rgba(103, 232, 249, 0.14);
          border: 1px solid rgba(103, 232, 249, 0.38);
          color: #67E8F9;
      }

      .source-badge-pageindex,
      .badge-pageindex {
          background: rgba(251, 191, 36, 0.14);
          border: 1px solid rgba(251, 191, 36, 0.38);
          color: var(--amber);
      }

      .source-badge-legal,
      .source-badge-news,
      .source-badge-pageindex,
      .badge-hybrid,
      .badge-pageindex,
      .badge-speed {
          padding: 3px 10px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 700;
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
            metadata = normalise_source_metadata(src.get("metadata", {}), f"document-{index}")
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
