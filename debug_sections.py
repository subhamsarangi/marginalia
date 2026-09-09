"""
Debug — print GROBID section headers for all corpus PDFs.
Usage: uv run python debug_sections.py
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from smoke_test_01_ingest import parse_pdf

for pdf in sorted(Path("corpus").glob("*.pdf")):
    print(f"\n--- {pdf.name} ---")
    sections, parser = parse_pdf(pdf)
    if not sections:
        print("  ERROR: no sections")
        continue
    for s in sections:
        print(f"  [{parser}] {s['section']!r}")
