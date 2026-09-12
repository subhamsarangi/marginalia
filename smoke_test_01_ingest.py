"""
Smoke test 01 — Ingest pipeline.
Runs one PDF through parse → classify → chunk → Qdrant push.
Usage: uv run python smoke_test_01_ingest.py corpus/A001.pdf
"""
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from grobid_check import wait_for_grobid
wait_for_grobid()

from marginalia.ingest.grobid_parser import parse_with_grobid
from marginalia.ingest.fallback_parser import parse_with_pymupdf
from marginalia.ingest.docling_parser import parse_with_docling
from marginalia.ingest.chunker import chunk_sections
from marginalia.ingest.vector_store import push_chunks
from marginalia.classify.classifier import get_discipline


def parse_pdf(pdf_path: Path) -> tuple[list[dict], str] | tuple[None, None]:
    """Returns (sections, parser_name) or (None, None) on total failure."""
    try:
        print("[GROBID] sending request...")
        sections = parse_with_grobid(pdf_path)
        if sections:
            print(f"[GROBID] {len(sections)} sections")
            return sections, "grobid"
    except Exception as e:
        print(f"[GROBID] failed: {e}")

    print("[pymupdf4llm] parsing...")
    sections = parse_with_pymupdf(pdf_path)
    if sections is not None:
        print(f"[pymupdf4llm] {len(sections)} sections")
        return sections, "pymupdf4llm"
    print("[pymupdf4llm] degenerate output, falling back to Docling")

    print("[Docling] parsing...")
    sections = parse_with_docling(pdf_path)
    if sections:
        print(f"[Docling] {len(sections)} sections")
        return sections, "docling"

    return None, None


def ingest(pdf_path: Path):
    print(f"\n--- Ingesting: {pdf_path.name} ---")

    sections, parser = parse_pdf(pdf_path)
    if not sections:
        print("ERROR: all parsers failed, no sections extracted")
        return

    # Classify discipline
    raw_text = " ".join(s["text"] for s in sections)
    print("[Classifier] classifying discipline...")
    discipline = get_discipline(sections, raw_text)
    print(f"[Classifier] discipline={discipline['discipline']!r} subtype={discipline.get('stem_subtype') or discipline.get('humanities_subtype')!r} method={discipline['method']!r} confidence={discipline['confidence']}")

    # Chunk
    print("[Chunker] chunking...")
    chunks = chunk_sections(sections, pdf_path, parser, discipline)
    print(f"[Chunker] {len(chunks)} chunks")

    # Preview first chunk
    first = chunks[0]
    print(f"[Preview] section={first['metadata']['section']!r} discipline={first['metadata']['discipline']!r} text={first['text'][:120]!r}")

    # Push to Qdrant
    print("[Qdrant] pushing chunks...")
    push_chunks(chunks)
    print(f"[Qdrant] pushed {len(chunks)} chunks for paper_id={pdf_path.stem!r}")


if __name__ == "__main__":
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus/A001.pdf")
    ingest(pdf)
