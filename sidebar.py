import streamlit as st
from theme import inject_theme


def render_sidebar():
    inject_theme()
    with st.sidebar:
        st.markdown(
            "<h3 style='font-family:Cinzel,serif;letter-spacing:0.1em;'>☽ Jung RAG ☾</h3>",
            unsafe_allow_html=True,
        )
        st.caption("Semantic search over Carl Jung's works")
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Books", "3")
        col2.metric("Chunks", "610")
        st.caption("Model: `all-MiniLM-L6-v2`")
        st.caption("Vector DB: ChromaDB")
