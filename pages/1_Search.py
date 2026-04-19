import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import streamlit as st
from rag_core import search, get_all_metadata
from sidebar import render_sidebar

st.set_page_config(page_title="Search — Jung RAG", page_icon="🔍", layout="wide")
render_sidebar()

st.title("🔍 Semantic Search")
st.markdown("Search across Jung's works using natural language. Results are ranked by semantic similarity.")

# ── Helpers ────────────────────────────────────────────────────────────────────
_STOPWORDS = {
    "the", "and", "for", "with", "what", "from", "this", "that", "these", "those",
    "was", "were", "been", "have", "has", "had", "into", "onto", "about", "their",
    "there", "which", "while", "where", "when", "your", "you", "are", "its",
    "not", "but", "all", "any", "one", "two", "does", "did",
}


def _query_terms(query: str) -> list[str]:
    """Non-trivial query words to highlight."""
    words = re.findall(r"[A-Za-zÀ-ÿ]+", query)
    return [w for w in words if len(w) >= 3 and w.lower() not in _STOPWORDS]


def highlight(text: str, query: str) -> str:
    """Wrap each query term occurrence with <mark>."""
    terms = _query_terms(query)
    if not terms:
        return text
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.IGNORECASE)
    return pattern.sub(r'<mark class="q">\1</mark>', text)


def key_sentence(text: str, query: str, window: int = 2) -> str:
    """Return first sentence containing a query term + 1 surrounding sentence."""
    terms_lc = [t.lower() for t in _query_terms(query)]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\[])", text)
    if not terms_lc:
        return " ".join(sentences[:window]).strip()
    for i, s in enumerate(sentences):
        s_lc = s.lower()
        if any(t in s_lc for t in terms_lc):
            end = min(len(sentences), i + window)
            return " ".join(sentences[i:end]).strip()
    return " ".join(sentences[:window]).strip() if sentences else text[:300]


def render_summary(results: list, query: str):
    """Show 1 key passage per unique book in top results."""
    seen_books = set()
    entries = []
    for text, meta, sim in results:
        title = meta["title"]
        if title in seen_books:
            continue
        seen_books.add(title)
        entries.append((text, meta, sim))
        if len(entries) >= 3:
            break

    st.markdown(
        f"<div style='font-family:Cinzel,serif;letter-spacing:0.08em;"
        f"color:#5C3317;margin:1rem 0 0.5rem 0;font-size:0.9rem;'>"
        f"❧ KEY PASSAGES ACROSS {len(entries)} VOLUME{'S' if len(entries)>1 else ''}"
        f"</div>",
        unsafe_allow_html=True,
    )
    for text, meta, sim in entries:
        snippet = highlight(key_sentence(text, query), query)
        st.markdown(
            f"""
            <div class="summary-card">
              <div class="summary-head">
                <span class="summary-book">{meta['title']}</span>
                <span class="summary-sim">{sim:.0f}% match</span>
              </div>
              <div class="summary-text">…{snippet}…</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Session state ──────────────────────────────────────────────────────────────
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# ── Query input ────────────────────────────────────────────────────────────────
query = st.text_input(
    "Enter your query",
    placeholder="e.g. individuation of the self",
    value=st.session_state.search_query,
)

# ── Filters (collapsible, below query) ─────────────────────────────────────────
with st.expander("⚙ Filters", expanded=False):
    meta = get_all_metadata()
    titles = sorted({m["title"] for m in meta})
    word_counts = [m["word_count"] for m in meta]
    wc_min_all, wc_max_all = min(word_counts), max(word_counts)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        book_filter = st.selectbox("Filter by book", ["All books"] + titles)
        filter_title = None if book_filter == "All books" else book_filter
    with col2:
        k = st.slider("Number of results", 1, 15, 5)
    with col3:
        score_threshold = st.slider("Min similarity %", 0, 80, 0)
    with col4:
        wc_range = st.slider(
            "Chunk size (words)",
            wc_min_all, wc_max_all,
            (wc_min_all, wc_max_all),
        )

# ── Action buttons ─────────────────────────────────────────────────────────────
col_btn, col_clear, _ = st.columns([1, 1, 6])
search_clicked = col_btn.button("Search", type="primary")
if col_clear.button("Clear"):
    st.session_state.search_query = ""
    st.session_state.search_results = []
    st.rerun()

if search_clicked and query.strip():
    st.session_state.search_query = query
    with st.spinner("Searching..."):
        results = search(query, k=k, filter_title=filter_title, score_threshold=score_threshold)
    st.session_state.search_results = [(doc.page_content, doc.metadata, sim) for doc, sim in results]

results = [
    (text, m, sim)
    for text, m, sim in st.session_state.search_results
    if wc_range[0] <= m["word_count"] <= wc_range[1]
]

# ── Results ────────────────────────────────────────────────────────────────────
if results:
    st.divider()

    # Summary card at top
    render_summary(results, st.session_state.search_query)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-family:Cinzel,serif;letter-spacing:0.08em;"
        f"color:#5C3317;margin:0.5rem 0;font-size:0.9rem;'>"
        f"✦ ALL RESULTS · {len(results)}</div>",
        unsafe_allow_html=True,
    )

    for text, meta, sim in results:
        color = "green" if sim >= 60 else "orange" if sim >= 30 else "red"
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.markdown(
                f"**{meta['title']}**  \n"
                f"_{meta.get('volume', '')}_ — Chunk {meta['chunk_index']+1}/{meta['total_chunks']}"
            )
            col2.markdown(f"📝 {meta['word_count']} words")
            col3.markdown(f":{color}[**{sim:.0f}%**]")
            with st.expander("Show full text"):
                st.markdown(highlight(text, st.session_state.search_query), unsafe_allow_html=True)
elif st.session_state.search_query:
    st.info("No results above the similarity threshold. Try lowering the minimum similarity.")
