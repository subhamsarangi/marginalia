from langchain_text_splitters import RecursiveCharacterTextSplitter

MAX_SECTION_SIZE = 1500
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def chunk_sections(sections: list[dict]) -> list[dict]:
    """Split oversized sections into chunks. Small sections pass through unchanged."""
    chunks = []
    for section in sections:
        text = section["text"]
        if len(text) <= MAX_SECTION_SIZE:
            chunks.append(section)
        else:
            for chunk_text in _splitter.split_text(text):
                chunks.append({**section, "text": chunk_text})
    return chunks
