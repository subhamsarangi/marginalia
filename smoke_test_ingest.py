"""
Smoke test: run one PDF through the full ingest pipeline and report results.
Usage: uv run python smoke_test_ingest.py corpus/A001.pdf
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from marginalia.ingest.grobid_parser import parse_with_grobid
from marginalia.ingest.fallback_parser import parse_with_pymupdf
from marginalia.ingest.docling_parser import parse_with_docling
from marginalia.ingest.chunker import chunk_sections
from marginalia.ingest.vector_store import push_chunks


def ingest(pdf_path: Path):
    print(f"\n--- Ingesting: {pdf_path.name} ---")

    # 1. Try GROBID
    sections, parser = None, None
    try:
        print("[GROBID] sending request...")
        sections = parse_with_grobid(pdf_path)
        parser = "grobid"
        print(f"[GROBID] {len(sections)} sections")
    except Exception as e:
        print(f"[GROBID] failed: {e}")

    # 2. pymupdf4llm fast pass
    if not sections:
        print("[pymupdf4llm] parsing...")
        sections = parse_with_pymupdf(pdf_path)
        if sections is not None:
            parser = "pymupdf4llm"
            print(f"[pymupdf4llm] {len(sections)} sections")
        else:
            print("[pymupdf4llm] degenerate output, falling back to Docling")

    # 3. Docling deep fallback
    if not sections:
        print("[Docling] parsing...")
        sections = parse_with_docling(pdf_path)
        parser = "docling"
        print(f"[Docling] {len(sections)} sections")

    if not sections:
        print("ERROR: all parsers failed, no sections extracted")
        return

    # 4. Chunk
    print("[Chunker] chunking...")
    chunks = chunk_sections(sections, pdf_path, parser)
    print(f"[Chunker] {len(chunks)} chunks")

    # 5. Preview first chunk
    first = chunks[0]
    print(f"[Preview] section={first['metadata']['section']!r} text={first['text'][:120]!r}")

    # 6. Push to Qdrant
    print("[Qdrant] pushing chunks...")
    push_chunks(chunks)
    print(f"[Qdrant] pushed {len(chunks)} chunks for paper_id={pdf_path.stem!r}")


if __name__ == "__main__":
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus/A001.pdf")
    ingest(pdf)
