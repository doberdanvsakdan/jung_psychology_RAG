import json
from pathlib import Path

import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

DOCUMENTS_PATH = Path("documents/all_documents.json")
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "jung_rag_main"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_documents_from_json(path: Path = DOCUMENTS_PATH) -> tuple[list[Document], list[dict]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    docs = []
    for entry in raw:
        meta = dict(entry["metadata"])
        meta["doc_id"] = entry["id"]
        docs.append(Document(page_content=entry["text"], metadata=meta))
    return docs, raw


@st.cache_data(show_spinner=False)
def get_all_metadata() -> list[dict]:
    with open(DOCUMENTS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [entry["metadata"] for entry in raw]


def _has_collection(chroma_dir: str, collection_name: str) -> bool:
    import chromadb
    try:
        client = chromadb.PersistentClient(path=chroma_dir)
        names = [c.name for c in client.list_collections()]
        return collection_name in names
    except Exception:
        return False


@st.cache_resource(show_spinner="Building knowledge base... (first run only, ~60s)")
def get_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    if _has_collection(CHROMA_DIR, COLLECTION_NAME):
        return Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

    docs, raw = load_documents_from_json()
    ids = [entry["id"] for entry in raw]
    return Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"},
        ids=ids,
    )


def search(
    query: str,
    k: int = 5,
    filter_title: str | None = None,
    score_threshold: float = 0.0,
) -> list[tuple[Document, float]]:
    vs = get_vectorstore()
    chroma_filter = {"title": filter_title} if filter_title else None
    results = vs.similarity_search_with_score(query, k=k, filter=chroma_filter)
    # score = cosine distance (0=identical); convert to similarity %
    out = []
    for doc, dist in results:
        similarity = max(0.0, (1 - dist) * 100)
        if similarity >= score_threshold:
            out.append((doc, similarity))
    return out
