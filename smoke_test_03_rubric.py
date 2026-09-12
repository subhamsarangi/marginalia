"""
Smoke test 03 — Rubric extraction.
Runs one STEM and one humanities paper through rubric extraction and prints results + cost.
Depends on: smoke_test_01_ingest.py (parse), smoke_test_02_classify.py (classify)
Usage: uv run python smoke_test_03_rubric.py
"""
import json
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from grobid_check import wait_for_grobid
wait_for_grobid()

from smoke_test_01_ingest import parse_pdf
from marginalia.classify.classifier import get_discipline
from marginalia.rubric.extractor import extract_rubric
from marginalia.rubric.store import save_rubric, get_rubric

total_usage = {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "cost_usd": 0.0}


def run(pdf_path: Path):
    print(f"\n--- {pdf_path.name} ---")
    sections, parser = parse_pdf(pdf_path)
    if not sections:
        print("  ERROR: no sections")
        return

    raw_text = " ".join(s["text"] for s in sections)
    discipline = get_discipline(sections, raw_text)
    print(f"  discipline : {discipline['discipline']} / {discipline.get('stem_subtype') or discipline.get('humanities_subtype')}")

    print("  extracting rubric...")
    rubric, usage = extract_rubric(sections, discipline["discipline"], discipline.get("stem_subtype"))
    print(f"  rubric     :\n{json.dumps(rubric, indent=4)}")
    print(f"  tokens     : input={usage['input_tokens']} output={usage['output_tokens']} thinking={usage['thinking_tokens']}")
    print(f"  cost       : ${usage['cost_usd']:.6f}")

    for k in total_usage:
        total_usage[k] += usage[k]

    print("  saving to Cosmos DB...")
    save_rubric(pdf_path.stem, rubric)

    print("  reading back from Cosmos DB...")
    stored = get_rubric(pdf_path.stem)
    print(f"  stored id  : {stored['id']}")


if __name__ == "__main__":
    for name in ["corpus/A001.pdf", "corpus/A003.pdf"]:
        run(Path(name))

    print(f"\n--- TOTAL ---")
    print(f"  input_tokens    : {total_usage['input_tokens']}")
    print(f"  output_tokens   : {total_usage['output_tokens']}")
    print(f"  thinking_tokens : {total_usage['thinking_tokens']}")
    print(f"  total cost      : ${total_usage['cost_usd']:.6f}")
