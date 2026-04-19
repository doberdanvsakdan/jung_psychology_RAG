import json
import re
from pathlib import Path
from pypdf import PdfReader

LITERATURE_DIR = Path("literature")
OUTPUT_DIR = Path("documents")
TARGET_WORDS = 600

BOOKS = [
    {
        "filename": "C.-G.-Jung-Collected-Works-Volume-9i_-The-Archetypes-of-the-Collective-Unconscious.pdf",
        "title": "The Archetypes and the Collective Unconscious",
        "author": "C.G. Jung",
        "volume": "Collected Works Vol. 9i",
        "split_mode": "jung_numbered",  # paragraphs marked [N]
    },
    {
        "filename": "Collected Works of C.G. Jung, Volume 6- Psychological Types.pdf",
        "title": "Psychological Types",
        "author": "C.G. Jung",
        "volume": "Collected Works Vol. 6",
        "split_mode": "jung_numbered",
    },
    {
        "filename": "Man and his Symbols - Carl G. Jung.pdf",
        "title": "Man and His Symbols",
        "author": "Carl G. Jung",
        "volume": "",
        "split_mode": "sentence",  # no [N] markers — split at sentence boundaries
    },
]


def extract_full_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        # Fix hyphenated line breaks (e.g. "uncon-\nscious" → "unconscious")
        text = re.sub(r"-\n(\w)", r"\1", text)
        # Join hard line wraps → single space
        text = re.sub(r"\n", " ", text)
        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)
        pages.append(text.strip())
    return " ".join(pages)


def looks_like_back_matter(text: str) -> bool:
    """Detect bibliography, index, and appendix chunks."""
    words = text.split()
    if not words:
        return False
    # Bibliography: many publication years + ALL-CAPS author names
    years = len(re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", text))
    allcaps = len(re.findall(r"\b[A-Z]{2,}\b", text))
    bib_ratio = (years + allcaps) / len(words)
    if bib_ratio > 0.15:
        return True
    # Index: high density of bare page numbers (e.g. "75 , 102 , 105 , 106")
    page_refs = len(re.findall(r"\b\d{1,4}\s*[,n]", text))
    index_ratio = page_refs / len(words)
    return index_ratio > 0.1


def split_jung_numbered(text: str) -> list[str]:
    """Split on Jung's own paragraph numbers: [1]–[999]. Skip year references [1800+]."""
    parts = re.split(r"\[(\d+)\]", text)
    # parts = [pre_text, num1, para1, num2, para2, ...]
    paragraphs = []
    i = 1
    while i < len(parts) - 1:
        num = int(parts[i])
        content = parts[i + 1].strip()
        # Skip year-like numbers (bibliography entries) and very short fragments
        if num >= 1500 or len(content.split()) < 10:
            i += 2
            continue
        if not looks_like_back_matter(content):
            paragraphs.append(f"[{num}] {content}")
        i += 2
    return paragraphs


def split_by_sentences(text: str, target_words: int = TARGET_WORDS) -> list[str]:
    """Split into ~target_words chunks at sentence boundaries."""
    # Split on sentence-ending punctuation followed by space + capital
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    chunks = []
    current = []
    current_words = 0

    for sentence in sentences:
        wc = len(sentence.split())
        if current_words + wc > target_words * 1.4 and current_words >= target_words * 0.5:
            chunks.append(" ".join(current))
            current = [sentence]
            current_words = wc
        else:
            current.append(sentence)
            current_words += wc

    if current:
        chunks.append(" ".join(current))
    return chunks


def sub_split(text: str, target_words: int) -> list[str]:
    """Break a single oversized block at sentence boundaries."""
    return split_by_sentences(text, target_words)


def group_paragraphs(paragraphs: list[str], target_words: int = TARGET_WORDS) -> list[str]:
    """Group Jung's numbered paragraphs into ~target_words chunks."""
    chunks = []
    current = []
    current_words = 0

    for para in paragraphs:
        wc = len(para.split())
        # A single paragraph already exceeds 2× target — break it up
        if wc > target_words * 2:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_words = 0
            chunks.extend(sub_split(para, target_words))
            continue
        if current_words + wc > target_words * 1.5 and current_words >= target_words * 0.5:
            chunks.append("\n\n".join(current))
            current = [para]
            current_words = wc
        else:
            current.append(para)
            current_words += wc

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def process_book(book: dict) -> list[dict]:
    pdf_path = LITERATURE_DIR / book["filename"]
    print(f"Processing: {book['title']} ...")

    text = extract_full_text(pdf_path)

    if book["split_mode"] == "jung_numbered":
        paragraphs = split_jung_numbered(text)
        print(f"  → {len(paragraphs)} numbered paragraphs")
        chunks = group_paragraphs(paragraphs)
    else:
        chunks = split_by_sentences(text)
        print(f"  → sentence-based splitting")

    documents = []
    for i, chunk in enumerate(chunks):
        word_count = len(chunk.split())
        documents.append({
            "id": f"{pdf_path.stem}_chunk_{i:04d}",
            "text": chunk,
            "metadata": {
                "title": book["title"],
                "author": book["author"],
                "volume": book["volume"],
                "source_file": book["filename"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "word_count": word_count,
            },
        })

    word_counts = [d["metadata"]["word_count"] for d in documents]
    avg = sum(word_counts) // len(word_counts) if word_counts else 0
    print(f"  → {len(chunks)} chunks | avg {avg} words | min {min(word_counts)} | max {max(word_counts)}")
    return documents


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_documents = []

    for book in BOOKS:
        docs = process_book(book)
        all_documents.extend(docs)

        safe_name = re.sub(r"[^\w]+", "_", book["title"].lower())
        book_path = OUTPUT_DIR / f"{safe_name}.json"
        with open(book_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        print(f"  Saved → {book_path}\n")

    combined_path = OUTPUT_DIR / "all_documents.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, ensure_ascii=False, indent=2)

    print(f"Done. Total chunks: {len(all_documents)}")
    print(f"Combined → {combined_path}")


if __name__ == "__main__":
    main()
