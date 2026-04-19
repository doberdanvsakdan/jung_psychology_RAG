import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import streamlit as st
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_core import EMBEDDING_MODEL, DOCUMENTS_PATH
from sidebar import render_sidebar

st.set_page_config(page_title="Compare — Jung RAG", page_icon="⚖️", layout="wide")
render_sidebar()

st.title("⚖️ Chunking Strategy Comparison")
st.markdown(
    "Compare four chunking strategies side-by-side. "
    "Each one rebuilds an in-memory vector index from the full book texts, "
    "so the same query can return different passages per strategy."
)

STRATEGIES = ["Recursive Character", "Fixed Character", "Token-based", "Semantic"]


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_book_texts() -> list[str]:
    """Reconstruct full per-book text by concatenating chunks in order."""
    with open(DOCUMENTS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    books: dict[str, list[tuple[int, str]]] = {}
    for e in raw:
        title = e["metadata"]["title"]
        idx = e["metadata"]["chunk_index"]
        books.setdefault(title, []).append((idx, e["text"]))
    texts = []
    for items in books.values():
        items.sort(key=lambda x: x[0])
        texts.append("\n\n".join(t for _, t in items))
    return texts


@st.cache_resource(show_spinner=False)
def _embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def _make_vs(docs, collection_name: str) -> Chroma:
    import chromadb
    client = chromadb.EphemeralClient()
    return Chroma.from_documents(
        documents=docs,
        embedding=_embeddings(),
        client=client,
        collection_name=collection_name,
        collection_metadata={"hnsw:space": "cosine"},
    )


# ── Index builders (cached per parameter combination) ──────────────────────────
@st.cache_resource(show_spinner=False)
def _build_recursive(chunk_size: int, chunk_overlap: int) -> tuple[Chroma, int]:
    texts = _load_book_texts()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.create_documents(texts)
    return _make_vs(docs, f"recursive_{chunk_size}_{chunk_overlap}"), len(docs)


@st.cache_resource(show_spinner=False)
def _build_character(chunk_size: int, chunk_overlap: int, separator: str) -> tuple[Chroma, int]:
    texts = _load_book_texts()
    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator=separator,
    )
    docs = splitter.create_documents(texts)
    sep_key = separator.replace("\n", "n").replace(" ", "sp") or "none"
    return _make_vs(docs, f"char_{chunk_size}_{chunk_overlap}_{sep_key}"), len(docs)


@st.cache_resource(show_spinner=False)
def _build_token(chunk_size: int, chunk_overlap: int) -> tuple[Chroma, int]:
    texts = _load_book_texts()
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = splitter.create_documents(texts)
    return _make_vs(docs, f"token_{chunk_size}_{chunk_overlap}"), len(docs)


@st.cache_resource(show_spinner=False)
def _build_semantic(breakpoint_type: str) -> tuple[Chroma, int]:
    texts = _load_book_texts()
    splitter = SemanticChunker(
        _embeddings(),
        breakpoint_threshold_type=breakpoint_type,
    )
    all_docs = []
    for text in texts:
        all_docs.extend(splitter.create_documents([text]))
    return _make_vs(all_docs, f"semantic_{breakpoint_type}"), len(all_docs)


def _build_for(name: str, params: dict) -> tuple[Chroma, int]:
    if name == "Recursive Character":
        return _build_recursive(params["chunk_size"], params["chunk_overlap"])
    if name == "Fixed Character":
        return _build_character(params["chunk_size"], params["chunk_overlap"], params["separator"])
    if name == "Token-based":
        return _build_token(params["chunk_size"], params["chunk_overlap"])
    if name == "Semantic":
        return _build_semantic(params["breakpoint_type"])
    raise ValueError(f"Unknown strategy: {name}")


def _run_search(vs: Chroma, query: str, k: int) -> list[tuple[str, float]]:
    results = vs.similarity_search_with_score(query, k=k)
    return [(doc.page_content, max(0.0, (1 - dist) * 100)) for doc, dist in results]


# ── Strategy UI ────────────────────────────────────────────────────────────────
SEPARATOR_MAP = {
    "Paragraph (\\n\\n)": "\n\n",
    "Line (\\n)": "\n",
    "Space": " ",
    "None (hard cut)": "",
}


def _strategy_controls(col, slot: str, default: str) -> tuple[str, dict, str]:
    """Render selector + param widgets for one panel. Returns (strategy, params, summary)."""
    with col:
        st.markdown(f"#### Panel {slot}")
        name = st.selectbox(
            "Strategy",
            STRATEGIES,
            index=STRATEGIES.index(default),
            key=f"strat_{slot}",
        )
        params: dict = {}
        if name == "Recursive Character":
            params["chunk_size"] = st.slider(
                "Chunk size (chars)", 200, 4000, 1500, 100, key=f"rc_size_{slot}"
            )
            params["chunk_overlap"] = st.slider(
                "Overlap (chars)", 0, 500, 150, 10, key=f"rc_ov_{slot}"
            )
            summary = f"{params['chunk_size']} chars · overlap {params['chunk_overlap']}"
            st.caption("Tries `\\n\\n` → `\\n` → `. ` → space → char")
        elif name == "Fixed Character":
            sep_choice = st.selectbox(
                "Separator",
                list(SEPARATOR_MAP.keys()),
                key=f"fc_sep_{slot}",
            )
            params["separator"] = SEPARATOR_MAP[sep_choice]
            params["chunk_size"] = st.slider(
                "Chunk size (chars)", 200, 4000, 1500, 100, key=f"fc_size_{slot}"
            )
            params["chunk_overlap"] = st.slider(
                "Overlap (chars)", 0, 500, 150, 10, key=f"fc_ov_{slot}"
            )
            summary = f"{sep_choice} · {params['chunk_size']} chars · overlap {params['chunk_overlap']}"
            st.caption("Splits only on the chosen separator.")
        elif name == "Token-based":
            params["chunk_size"] = st.slider(
                "Chunk size (tokens)", 50, 1000, 400, 50, key=f"tk_size_{slot}"
            )
            params["chunk_overlap"] = st.slider(
                "Overlap (tokens)", 0, 200, 50, 10, key=f"tk_ov_{slot}"
            )
            summary = f"{params['chunk_size']} tokens · overlap {params['chunk_overlap']}"
            st.caption("Counts GPT-style tokens (tiktoken).")
        else:  # Semantic
            params["breakpoint_type"] = st.selectbox(
                "Breakpoint method",
                ["percentile", "standard_deviation", "interquartile"],
                key=f"sem_bp_{slot}",
            )
            summary = f"breakpoint: {params['breakpoint_type']}"
            st.caption("Splits where sentence embeddings diverge. Slow on first build.")
    return name, params, summary


# ── Top-level inputs ───────────────────────────────────────────────────────────
query = st.text_input("Query for comparison", placeholder="e.g. individuation and the self")
k = st.slider("Results per strategy", 1, 8, 3)

st.divider()

# Strategy configuration panels
cfg_cols = st.columns(3)
strat_a, params_a, sum_a = _strategy_controls(cfg_cols[0], "A", "Recursive Character")
strat_b, params_b, sum_b = _strategy_controls(cfg_cols[1], "B", "Token-based")
strat_c, params_c, sum_c = _strategy_controls(cfg_cols[2], "C", "Semantic")

st.divider()

if st.button("Compare", type="primary") and query.strip():
    result_cols = st.columns(3)
    panels = [
        (result_cols[0], "A", strat_a, params_a, sum_a),
        (result_cols[1], "B", strat_b, params_b, sum_b),
        (result_cols[2], "C", strat_c, params_c, sum_c),
    ]
    for col, slot, strat, params, summary in panels:
        with col:
            st.markdown(f"### {slot} · {strat}")
            st.caption(summary)
            with st.spinner(f"Building {strat} index..."):
                vs, chunk_count = _build_for(strat, params)
            st.caption(f"📊 {chunk_count} total chunks")
            results = _run_search(vs, query, k)
            for text, sim in results:
                with st.container(border=True):
                    st.markdown(f"**{sim:.0f}% match** · {len(text.split())} words")
                    preview = text[:400] + ("..." if len(text) > 400 else "")
                    st.markdown(preview)

st.divider()
st.info(
    "**Tip:** Keep the same strategy in two panels with different chunk sizes "
    "to isolate the effect of size. Or put Recursive vs Semantic side-by-side "
    "with comparable sizes to see how breakpoint logic changes the matched passages."
)
