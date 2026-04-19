# Arcana Psychologica — Jung RAG Knowledge Base

A semantic search application over the collected works of **Carl Gustav Jung**, built with Streamlit, LangChain, and ChromaDB. Search through 610 passages from three of Jung's most influential books using natural language queries.

**Live app**: https://jung-psychology-rag.onrender.com

---

## What This App Does

- **Semantic search** across 3 Jung books — finds passages by meaning, not keywords
- **Query highlighting** — matched terms are highlighted in the full text
- **Summary cards** — shows the most relevant passage per book at the top of results
- **Chunking comparison** — compare 4 different text splitting strategies side-by-side (Recursive, Fixed Character, Token-based, Semantic)
- **Statistics** — chunk distribution charts per book
- **Visualization** — keyword heatmap and concept similarity scatter across Jungian concepts
- **Parchment aesthetic** — custom CSS theme with IM Fell English + Cinzel fonts

## Books Indexed

| Title | Series | Year | Chunks |
|---|---|---|---|
| The Archetypes and the Collective Unconscious | Collected Works Vol. 9i | 1959 | 170 |
| Psychological Types | Collected Works Vol. 6 | 1921 | 266 |
| Man and His Symbols | Popular edition | 1964 | 174 |
| **Total** | | | **610** |

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | Streamlit |
| Vector database | ChromaDB (cosine distance) |
| Embedding model | `all-MiniLM-L6-v2` (sentence-transformers) |
| Orchestration | LangChain |
| PDF extraction | pypdf |
| Charts | Plotly Express |
| Deployment | Render.com |

---

## Run Locally

### Prerequisites
- Python 3.10+
- The 3 Jung PDF files placed in `literature/` (not included in repo due to copyright)

### Setup

```bash
# Clone the repo
git clone https://github.com/doberdanvsakdan/jung_psychology_RAG.git
cd jung_psychology_RAG

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### Prepare documents

Place the 3 PDF books in the `literature/` folder, then run:

```bash
python create_documents.py
```

This extracts text from the PDFs, applies the custom chunking strategy, and saves 610 chunks to `documents/all_documents.json`.

### Start the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

> On first run the app builds the ChromaDB vector index (~60 seconds). Subsequent starts load the cached index instantly.

---

## Project Structure

```
├── app.py                          # Home page + vectorstore warm-up
├── rag_core.py                     # ChromaDB init, embeddings, search
├── sidebar.py                      # Shared sidebar component
├── theme.py                        # Parchment CSS theme
├── create_documents.py             # PDF → chunks → JSON preprocessing
├── pages/
│   ├── 1_Search.py                 # Semantic search (main feature)
│   ├── 2_Compare.py                # Chunking strategy comparison
│   ├── 3_Statistics.py             # Chunk distribution charts
│   ├── 4_Visualization.py          # Keyword heatmap + concept scatter
│   └── 5_About.py                  # Project info and methodology
├── documents/
│   └── all_documents.json          # 610 pre-processed chunks
├── requirements.txt
├── render.yaml                     # Render.com deployment config
└── .gitignore
```

---

## Chunking Strategy

Rather than a generic character splitter, we use a **structure-aware, domain-specific** approach:

- **Collected Works (Vol. 9i + Vol. 6)**: split on Jung's own numbered paragraph markers `[N]`, filter out bibliography and index entries, then group paragraphs into ~600-word chunks
- **Man and His Symbols**: sentence-boundary splitter grouped to ~600 words (no paragraph numbers in this edition)

The target of 600 words balances context (enough for a complete argument) with embedding precision (focused enough for a single 384-dim vector).

---

## Author

Sergej Asic — AI Course Final Project, April 2026
