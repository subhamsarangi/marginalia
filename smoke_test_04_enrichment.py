"""
Smoke test 04 — External enrichment.
Resolves papers via Semantic Scholar, classifies citation sentiment with Gemini.
Depends on: smoke_test_01_ingest.py (parse), smoke_test_02_classify.py (classify)
Usage: uv run python smoke_test_04_enrichment.py
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
from marginalia.enrichment.enricher import enrich_paper
from marginalia.enrichment.store import save_enrichment, get_enrichment

total_usage = {
    "input_tokens": 0,
    "output_tokens": 0,
    "thinking_tokens": 0,
    "cost_usd": 0.0,
}


def run(pdf_path: Path):
    print(f"\n--- {pdf_path.name} ---")
    sections, _, identifiers = parse_pdf(pdf_path)
    if not sections:
        print("  ERROR: no sections")
        return

    title = identifiers.get("title")
    print(f"  title      : {title!r}")

    print("  enriching...")
    enrichment, usage = enrich_paper(
        paper_id=pdf_path.stem,
        title=title,
        arxiv_id=identifiers.get("arxiv"),
        doi=identifiers.get("doi"),
    )

    if enrichment.get("error"):
        print(f"  ERROR      : {enrichment['error']}")
        return

    print(f"  s2_id      : {enrichment['s2_id']}")
    print(f"  citations  : {enrichment['citation_count']}")
    web_mentions = enrichment.get("web_mentions") or []
    print(f"  web hits   : {len(web_mentions)}")
    for i, hit in enumerate(web_mentions[:3]):
        print(f"  [{i+1}] {hit.get('title')!r} -> {hit.get('url')}")
        print(f"       source     : {hit.get('source')}")
        print(f"       credible   : {hit.get('credible')}")

    # Preview first 2 citations with context + sentiment
    for i, c in enumerate(enrichment["citations"][:2]):
        print(f"  [{i+1}] {c['citing_title']!r} ({c['citing_year']})")
        print(f"       intents     : {c['intents']}")
        print(f"       influential : {c['is_influential']}")
        for ctx, sent in zip(c["contexts"], c["sentiments"]):
            print(f"       context     : {ctx[:120]!r}")
            print(f"       sentiment   : {sent}")

    print(
        f"  tokens     : input={usage['input_tokens']} output={usage['output_tokens']} thinking={usage['thinking_tokens']}"
    )
    print(f"  cost       : ${usage['cost_usd']:.6f}")

    for k in total_usage:
        total_usage[k] += usage[k]

    print("  saving to Cosmos DB...")
    save_enrichment(pdf_path.stem, enrichment)

    print("  reading back from Cosmos DB...")
    stored = get_enrichment(pdf_path.stem)
    print(f"  stored id  : {stored['id']}")


if __name__ == "__main__":
    # Test one STEM and one humanities paper
    for name in ["corpus/A002.pdf", "corpus/A004.pdf"]:
        run(Path(name))

    print(f"\n--- TOTAL ---")
    print(f"  input_tokens    : {total_usage['input_tokens']}")
    print(f"  output_tokens   : {total_usage['output_tokens']}")
    print(f"  thinking_tokens : {total_usage['thinking_tokens']}")
    print(f"  total cost      : ${total_usage['cost_usd']:.6f}")
