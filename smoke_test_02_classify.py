"""
Smoke test 02 — Discipline classification.
Runs all corpus PDFs through classify and prints discipline + subtype for each.
Usage: uv run python smoke_test_02_classify.py
"""
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from grobid_check import wait_for_grobid
wait_for_grobid()

from smoke_test_01_ingest import parse_pdf
from marginalia.classify.classifier import get_discipline


if __name__ == "__main__":
    for pdf in sorted(Path("corpus").glob("*.pdf")):
        print(f"\n--- {pdf.name} ---")
        sections, parser = parse_pdf(pdf)
        if not sections:
            print("  ERROR: no sections extracted")
            continue
        raw_text = " ".join(s["text"] for s in sections)
        result = get_discipline(sections, raw_text)
        subtype = result.get("stem_subtype") or result.get("humanities_subtype")
        print(f"  parser     : {parser}")
        print(f"  discipline : {result['discipline']}")
        print(f"  subtype    : {subtype}")
        print(f"  method     : {result['method']}")
        print(f"  confidence : {result['confidence']}")
