import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from rag_core import get_all_metadata, search
from sidebar import render_sidebar

st.set_page_config(page_title="Visualization — Jung RAG", page_icon="🎨", layout="wide")
render_sidebar()

st.title("🎨 Visualization")

tab1, tab2 = st.tabs(["Keyword Heatmap", "Concept Similarity"])

# ── Tab 1: Keyword Heatmap ────────────────────────────────────────────────────
with tab1:
    st.subheader("Top Keywords by Book")
    st.caption("Most frequent non-stopword terms in each book's chunks.")

    STOPWORDS = {
        "the","a","an","and","or","but","in","on","of","to","for","is","are","was",
        "were","be","been","being","have","has","had","do","does","did","will","would",
        "could","should","may","might","shall","it","its","this","that","these","those",
        "with","by","from","at","as","not","no","so","if","than","then","when","which",
        "who","what","he","she","they","we","i","his","her","their","our","my","your",
        "one","all","more","also","such","any","there","can","into","about","only","other",
        "up","out","even","very","just","some","both","how","each","between","through",
        "after","before","without","while","because","though","therefore","thus","yet",
        "however","since","must","much","most","well","over","new","own","same","way",
        "see","said","say","get","make","come","go","know","think","give","take","use",
    }

    @st.cache_data(show_spinner=False)
    def compute_keyword_matrix(top_n: int = 25):
        import json
        from pathlib import Path as P
        with open(P("documents/all_documents.json"), encoding="utf-8") as f:
            raw = json.load(f)

        book_words: dict[str, dict[str, int]] = {}
        for entry in raw:
            title = entry["metadata"]["title"]
            words = re.findall(r"[a-z]{4,}", entry["text"].lower())
            freq = book_words.setdefault(title, {})
            for w in words:
                if w not in STOPWORDS:
                    freq[w] = freq.get(w, 0) + 1

        # Pick global top_n words across all books
        global_freq: dict[str, int] = {}
        for freq in book_words.values():
            for w, c in freq.items():
                global_freq[w] = global_freq.get(w, 0) + c
        top_words = sorted(global_freq, key=lambda w: -global_freq[w])[:top_n]

        books = list(book_words.keys())
        matrix = []
        for title in books:
            row_total = sum(book_words[title].get(w, 0) for w in top_words) or 1
            matrix.append([book_words[title].get(w, 0) / row_total for w in top_words])

        return books, top_words, matrix

    top_n = st.slider("Number of keywords", 10, 40, 25)
    books, top_words, matrix = compute_keyword_matrix(top_n)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=top_words,
        y=[b.split(":")[0][:35] for b in books],
        colorscale="Blues",
        text=[[f"{v:.3f}" for v in row] for row in matrix],
        hovertemplate="Book: %{y}<br>Word: %{x}<br>Relative freq: %{z:.4f}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        xaxis=dict(tickangle=-40, tickfont=dict(size=11)),
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Color = relative frequency within each book (normalized per row).")


# ── Tab 2: Concept Similarity Scatter ────────────────────────────────────────
with tab2:
    st.subheader("Concept Similarity Across Books")
    st.caption(
        "Select a Jungian concept. Each dot is a chunk; "
        "Y = semantic similarity to the concept, X = chunk length, color = book."
    )

    CONCEPTS = [
        "shadow", "anima and animus", "archetype", "individuation",
        "collective unconscious", "persona", "synchronicity", "self",
    ]

    concept = st.selectbox("Concept", CONCEPTS)
    k_scatter = st.slider("Chunks to retrieve", 10, 60, 30)

    if st.button("Search concept", type="primary"):
        with st.spinner(f"Searching for '{concept}'..."):
            results = search(concept, k=k_scatter)

        rows = []
        for doc, sim in results:
            rows.append({
                "Book": doc.metadata["title"],
                "Similarity %": round(sim, 1),
                "Words": doc.metadata["word_count"],
                "Preview": doc.page_content[:120] + "...",
                "Chunk": f"#{doc.metadata['chunk_index']+1}",
            })
        df = pd.DataFrame(rows)

        fig = px.scatter(
            df, x="Words", y="Similarity %",
            color="Book", hover_data=["Chunk", "Preview"],
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=12,
        )
        fig.update_layout(height=420, legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df[["Book", "Chunk", "Similarity %", "Words", "Preview"]],
            use_container_width=True, hide_index=True,
        )
