from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

MAX_SECTION_SIZE = 1500
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def chunk_sections(sections: list[dict], pdf_path: Path, parser: str) -> list[dict]:
    """Split oversized sections and attach metadata to every chunk."""
    paper_id = pdf_path.stem
    chunks = []
    for section in sections:
        text = section["text"]
        base_meta = {
            "paper_id": paper_id,
            "section": section.get("section", "unknown"),
            "page": section.get("page"),
            "parser": parser,
        }
        if len(text) <= MAX_SECTION_SIZE:
            chunks.append({"text": text, "metadata": base_meta})
        else:
            for chunk_text in _splitter.split_text(text):
                chunks.append({"text": chunk_text, "metadata": base_meta})
    return chunks
