# Arcana Psychologica — RAG Knowledge Base Report
**Course**: AI Course — Final Project  
**Author**: Sergej Asic  
**Date**: April 2026  
**GitHub**: https://github.com/doberdanvsakdan/jung_psychology_RAG  
**Render**: https://jung-psychology-rag.onrender.com

---

## Page 1: Application Overview

### Topic

*Arcana Psychologica* is a semantic search application over the collected works of **Carl Gustav Jung** — the Swiss psychiatrist and founder of analytical psychology. The app allows users to search through three of Jung's most influential books using natural language queries, retrieving the most semantically relevant passages.

I chose this topic because Jung's works are dense, cross-referential, and difficult to navigate linearly. A semantic search engine is genuinely useful here: concepts like *anima*, *individuation*, and *the shadow* appear across all three volumes in subtly different contexts, and keyword search would miss most of the meaningful connections.

### Links

- **GitHub repository**: https://github.com/doberdanvsakdan/jung_psychology_RAG  
- **Live application (Render)**: _[add after deploy]_

---

## Page 2: Technical Details

### Documents

**Source material**: 3 books by Carl G. Jung, sourced as PDF editions of the published translations.

| Title | Series | Year | Chunks |
|---|---|---|---|
| The Archetypes and the Collective Unconscious | Collected Works Vol. 9i | 1959 | 170 |
| Psychological Types | Collected Works Vol. 6 | 1921 | 266 |
| Man and His Symbols | Popular edition | 1964 | 174 |
| **Total** | | | **610** |

The PDFs were extracted using `pypdf`, with hyphenated line breaks repaired and hard wraps collapsed into single spaces.

---

### Chunking Strategy

This is the most technically interesting part of the project, because a generic character-count splitter would have destroyed the semantic structure of these texts.

#### The Problem with Standard Splitters

Jung's *Collected Works* (Vol. 9i and Vol. 6) are formatted with **numbered paragraphs** — every logical unit of thought is preceded by a marker like `[1]`, `[2]`, ... `[999]`. These are not arbitrary numbers: each numbered block corresponds to one complete idea, argument, or clinical example. Splitting mid-paragraph would cut a thought in half.

Additionally, both volumes end with a **bibliography** and **index** containing entries like:

> `[1946] JUNG, C.G. 75, 102, 105, 106 ...`

These are useless for semantic search and would pollute the vector index with noise.

#### Strategy 1: Jung-Numbered Paragraph Grouping (Vol. 9i + Vol. 6)

1. **Split on `[N]` markers** using regex: `re.split(r"\[(\d+)\]", text)`
2. **Filter out year-like numbers** (`N >= 1500`) — these are bibliography citations, not paragraph numbers
3. **Filter back-matter** using a pattern detector: paragraphs with >15% density of publication years + ALL-CAPS author names (bibliography) or >10% bare page references (index)
4. **Group filtered paragraphs** to a target of ~600 words, never cutting mid-paragraph. If a single paragraph exceeds 1200 words, it is sub-split at sentence boundaries.

This produced **natural, semantically coherent chunks** that preserve Jung's own logical structure. The target of ~600 words balances context (enough for a complete argument) with precision (not so much that an unrelated idea drowns the query).

**Chunk size used**: ~600 words / ~3,600 characters average  
**Overlap**: none — because paragraph boundaries are hard semantic breaks; overlap would merge unrelated arguments

#### Strategy 2: Sentence-Boundary Grouping (Man and His Symbols)

*Man and His Symbols* has no numbered paragraphs (it is a popular, illustrated edition). Here we used a sentence-boundary splitter:

1. Split on sentence-ending punctuation followed by a capital letter: `(?<=[.!?])\s+(?=[A-Z])`
2. Group sentences into ~600-word chunks, respecting a tolerance of ±40%
3. Never cut mid-sentence

**Chunk size**: ~600 words target  
**Overlap**: none

#### Why ~600 Words?

- **Too small (100–200 words)**: Jung's arguments span multiple sentences. A chunk of 150 words might capture the conclusion without the premise, making retrieval context-poor.
- **Too large (1000+ words)**: The embedding model compresses everything into a single 384-dimensional vector. A 1200-word chunk discussing both *anima* and *individuation* will have a diluted embedding that ranks lower for specific queries than a focused 600-word chunk.
- **600 words**: Covers one complete logical unit (typically 2–4 numbered paragraphs), fits comfortably in the model's context window, and keeps the embedding semantically focused.

#### Comparison Across Strategies (Compare Page)

The app includes a **Compare page** where four chunking strategies can be tested side-by-side on the same query:

| Strategy | Chunk unit | Query: "individuation of the self" |
|---|---|---|
| **Recursive Character** (1500 chars) | Character count, hierarchical separators | Returns dense definitions; cuts mid-sentence occasionally |
| **Fixed Character** (1500 chars, `\n\n` separator) | Hard paragraph break | Cleaner breaks, but shorter passages where paragraphs are short |
| **Token-based** (400 tokens ≈ 300 words) | GPT token count | More chunks, higher precision for single-concept queries; loses surrounding context |
| **Semantic** (percentile breakpoints) | Embedding distance between sentences | Longest coherent passages; best for conceptual queries; slowest to build (~2 min) |

**Concrete example**: Searching "collective unconscious and archetypes" with Token-based (400 tokens) returned a passage focused only on the definition. The same query with Semantic chunking returned the definition *plus* three clinical examples that followed in the original text — more useful for understanding the concept in depth.

---

### Embedding Model

**Model**: `all-MiniLM-L6-v2` (sentence-transformers)  
**Dimensions**: 384  
**RAM usage**: ~90 MB  
**Language**: English (all three Jung books are English translations)

The model was chosen over multilingual alternatives (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) because all source texts are in English and the smaller, language-specific model produces better cosine similarity scores for English text at lower memory cost — critical for the Render.com free tier (512 MB RAM limit).

**Vector database**: ChromaDB with **cosine distance** (`hnsw:space: cosine`). The default L2 (Euclidean) distance was intentionally overridden because sentence-transformer embeddings are normalized — cosine similarity is the correct metric and produces intuitive percentage scores: `similarity% = (1 - cosine_distance) * 100`.

---

### Interesting Findings

- **Out-of-domain queries return low scores**: Searching "pizza recipe" returns results below 20% similarity, confirming the model correctly distinguishes domain relevance.
- **"Shadow"** (a key Jungian concept) returned 62% matches — notably higher than searching "dark side of personality" (48%), despite conveying the same idea. Jung's own terminology embeds more tightly than paraphrases.
- **Bibliography pollution**: The first version of the app included bibliography entries as chunks, causing searches for author names like "FREUD" to return citation lists instead of actual content. The back-matter filter resolved this.
- **Cosine vs. L2 bug**: The initial deployment used ChromaDB's default L2 distance. Searching "anima" returned 1% similarity despite highly relevant results. Switching to cosine distance corrected this to 50–65% for the same query — the most impactful single fix of the project.

---

## Page 3: Reflections & Extensions

### What I Learned

- Chunking is not a hyperparameter to tune randomly — the best chunking strategy is derived from the **structure of the source documents**. Jung's numbered paragraphs were a gift; most corpora require more creative boundary detection.
- Vector distance metrics matter fundamentally. Using the wrong metric (L2 instead of cosine) for normalized embeddings produces scores that are mathematically meaningless.
- Streamlit's `@st.cache_resource` is essential for RAG apps — rebuilding a 610-document vector index on every page interaction would make the app unusable.

### What I Would Improve

- **LLM answer generation**: Currently the app only retrieves passages. Adding a language model (e.g., Claude via the Anthropic API) to synthesize a direct answer from the top-k chunks would turn this into a full RAG pipeline.
- **Persistent vector store on Render**: The free tier's ephemeral filesystem means ChromaDB is rebuilt on every cold start (~60 seconds). Integrating a managed vector database (e.g., Pinecone, Weaviate) would eliminate this delay.
- **PDF upload**: Allowing users to upload their own Jung texts or related works would make the archive extensible without code changes.
- **Cross-volume concept tracking**: A visualization showing how the frequency and context of key concepts (shadow, anima, self) evolves across Jung's career (Vol. 6 → Vol. 9i → Man and His Symbols) would add genuine scholarly value.

---

## Technical Stack Summary

| Component | Technology |
|---|---|
| Web framework | Streamlit |
| Vector database | ChromaDB (cosine distance) |
| Embedding model | all-MiniLM-L6-v2 (sentence-transformers) |
| LangChain modules | langchain-community, langchain-text-splitters, langchain-experimental |
| PDF extraction | pypdf |
| Charts | Plotly Express |
| Deployment | Render.com (Python web service) |
| Version control | Git / GitHub |
