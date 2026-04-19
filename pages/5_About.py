import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from sidebar import render_sidebar

st.set_page_config(page_title="About — Jung RAG", page_icon="ℹ️", layout="wide")
render_sidebar()

st.title("ℹ️ About this Project")

st.markdown("""
This application was built as a final project for an AI course. The goal was to construct
a **Retrieval-Augmented Generation (RAG)** knowledge base over a domain of personal interest —
in this case, the analytical psychology of **Carl Gustav Jung**.

Rather than using a generative LLM to produce answers, this app focuses on the retrieval component:
given a natural language query, it finds the most semantically relevant passages from Jung's writings
using vector embeddings and cosine similarity.
""")

st.divider()
st.subheader("Books in the Knowledge Base")

books = pd.DataFrame([
    {
        "Title": "The Archetypes and the Collective Unconscious",
        "Author": "C.G. Jung",
        "Series": "Collected Works Vol. 9i",
        "First published": 1959,
        "Chunks": 170,
    },
    {
        "Title": "Psychological Types",
        "Author": "C.G. Jung",
        "Series": "Collected Works Vol. 6",
        "First published": 1921,
        "Chunks": 266,
    },
    {
        "Title": "Man and His Symbols",
        "Author": "Carl G. Jung et al.",
        "Series": "Popular edition",
        "First published": 1964,
        "Chunks": 174,
    },
])
st.dataframe(books, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Chunking Methodology")
st.markdown("""
Preprocessing was done in a separate script (`create_documents.py`) before deploying the app,
so the PDFs are never needed at runtime — only the pre-processed JSON file.

**Two strategies were used:**

1. **Jung's numbered paragraphs** (Collected Works volumes)
   Jung's Collected Works use a scholarly paragraph numbering system: `[1]`, `[2]`, `[3]`…
   Each numbered paragraph represents a complete, self-contained thought.
   The script splits on these markers, then **groups consecutive paragraphs** until the chunk
   reaches ~600 words. This preserves the philosophical coherence of Jung's argumentation.

2. **Sentence-boundary splitting** (Man and His Symbols)
   This popular edition does not use numbered paragraphs. Instead, the script splits on
   sentence-ending punctuation followed by a capital letter, then accumulates sentences
   until ~600 words are reached. This avoids cutting mid-thought.

**Filtering:** Bibliography entries, index pages, and footnote-heavy sections were automatically
detected and excluded (high density of year numbers and page references = back-matter).

**Result:** 610 chunks averaging ~777 words each, covering the full content of three books.
""")

st.divider()
st.subheader("Technical Stack")

stack = pd.DataFrame([
    {"Component": "UI Framework", "Technology": "Streamlit 1.56"},
    {"Component": "Embeddings", "Technology": "all-MiniLM-L6-v2 (Sentence Transformers)"},
    {"Component": "Vector Database", "Technology": "ChromaDB (persistent on disk)"},
    {"Component": "RAG Framework", "Technology": "LangChain + LangChain Community"},
    {"Component": "PDF Parsing", "Technology": "pypdf (offline, preprocessing only)"},
    {"Component": "Visualizations", "Technology": "Plotly Express"},
    {"Component": "Deployment", "Technology": "Render.com (free tier)"},
    {"Component": "Language", "Technology": "Python 3.13"},
])
st.dataframe(stack, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Why all-MiniLM-L6-v2?")
st.markdown("""
- All three books are written in **English** → no need for a multilingual model
- Model size: **~90 MB** — well within Render free tier RAM limits
- Embedding dimension: **384** — fast and efficient for 610 chunks
- Strong performance on semantic similarity tasks for academic/philosophical text
""")

st.divider()
st.caption("Built for AI Course Final Project · 2026")
