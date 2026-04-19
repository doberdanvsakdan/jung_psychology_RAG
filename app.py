import streamlit as st

st.set_page_config(
    page_title="Jung RAG — Arcana Psychologica",
    page_icon="☽",
    layout="wide",
    initial_sidebar_state="expanded",
)

from rag_core import get_all_metadata, get_vectorstore
from sidebar import render_sidebar

render_sidebar()

with st.spinner("Awakening the collective unconscious..."):
    get_vectorstore()

st.markdown(
    "<div class='ornament'>✦ ✦ ✦</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h1 style='text-align:center;font-family:Cinzel,serif;letter-spacing:0.12em;'>"
    "Arcana Psychologica</h1>"
    "<p style='text-align:center;font-style:italic;font-size:1.1rem;color:#5C3317;'>"
    "A Semantic Archive of the Works of Carl Gustav Jung"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='ornament'>❧ &nbsp; ❧ &nbsp; ❧</div>",
    unsafe_allow_html=True,
)

st.divider()

meta = get_all_metadata()
books = {}
for m in meta:
    t = m["title"]
    books[t] = books.get(t, 0) + 1
total_words = sum(m["word_count"] for m in meta)
avg_words = total_words // len(meta)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Volumes", len(books))
col2.metric("Passages", len(meta))
col3.metric("Avg Words / Passage", avg_words)
col4.metric("Total Words", f"{total_words:,}")

st.divider()
st.subheader("Volumes in the Archive")

import pandas as pd

book_info = [
    {
        "Title": "The Archetypes and the Collective Unconscious",
        "Series": "Collected Works Vol. 9i",
        "Year": 1959,
        "Passages": books.get("The Archetypes and the Collective Unconscious", 0),
    },
    {
        "Title": "Psychological Types",
        "Series": "Collected Works Vol. 6",
        "Year": 1921,
        "Passages": books.get("Psychological Types", 0),
    },
    {
        "Title": "Man and His Symbols",
        "Series": "Popular edition",
        "Year": 1964,
        "Passages": books.get("Man and His Symbols", 0),
    },
]

st.dataframe(pd.DataFrame(book_info), use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    "<p style='text-align:center;font-style:italic;color:#5C3317;'>"
    "Navigate the passages of the unconscious through the <b>Search</b> page. "
    "Compare retrieval methods in <b>Compare</b>. Explore patterns in <b>Statistics</b> and <b>Visualization</b>."
    "</p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='ornament'>✦ ✦ ✦</div>", unsafe_allow_html=True)
