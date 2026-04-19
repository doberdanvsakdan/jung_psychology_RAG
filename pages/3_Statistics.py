import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from rag_core import get_all_metadata
from sidebar import render_sidebar

st.set_page_config(page_title="Statistics — Jung RAG", page_icon="📊", layout="wide")
render_sidebar()

st.title("📊 Knowledge Base Statistics")

meta = get_all_metadata()
df = pd.DataFrame(meta)

# --- Chunks per book ---
st.subheader("Chunks per Book")
book_counts = df.groupby("title").size().reset_index(name="chunks")
fig1 = px.bar(
    book_counts,
    x="chunks", y="title",
    orientation="h",
    color="title",
    text="chunks",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig1.update_layout(showlegend=False, yaxis_title="", xaxis_title="Number of Chunks", height=250)
fig1.update_traces(textposition="outside")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- Word count distribution ---
st.subheader("Word Count Distribution")
col1, col2 = st.columns(2)

with col1:
    mean_wc = df["word_count"].mean()
    median_wc = df["word_count"].median()
    fig2 = px.histogram(
        df, x="word_count", color="title",
        nbins=40, barmode="overlay", opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"word_count": "Words per Chunk", "title": "Book"},
    )
    fig2.add_vline(x=mean_wc, line_dash="dash", line_color="black", annotation_text=f"Mean {mean_wc:.0f}")
    fig2.add_vline(x=median_wc, line_dash="dot", line_color="gray", annotation_text=f"Median {median_wc:.0f}")
    fig2.update_layout(height=350, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    fig3 = px.box(
        df, x="title", y="word_count", color="title",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"word_count": "Words per Chunk", "title": "Book"},
    )
    fig3.update_layout(showlegend=False, xaxis_title="", height=350,
                       xaxis=dict(tickangle=-15))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# --- Summary table ---
st.subheader("Summary by Book")
summary = df.groupby("title")["word_count"].agg(
    Chunks="count", Mean="mean", Median="median", Min="min", Max="max", Total="sum"
).round(0).astype(int).reset_index()
summary.columns = ["Book", "Chunks", "Avg Words", "Median Words", "Min", "Max", "Total Words"]
st.dataframe(summary, use_container_width=True, hide_index=True)
