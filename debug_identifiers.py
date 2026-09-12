"""
Debug — extract identifiers (DOI, arXiv ID, PMID, etc.) from GROBID TEI-XML.
Usage: uv run python debug_identifiers.py
"""
import sys
import httpx
from pathlib import Path
from xml.etree import ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

from grobid_check import wait_for_grobid

GROBID_URL = "http://localhost:8070"
TEI_NS = "http://www.tei-c.org/ns/1.0"

wait_for_grobid()

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus")


def extract_ids(tei_xml: str) -> dict:
    root = ET.fromstring(tei_xml)
    ids = {}
    for id_el in root.iter(f"{{{TEI_NS}}}idno"):
        id_type = id_el.get("type", "unknown").lower()
        if id_el.text:
            ids[id_type] = id_el.text.strip()
    return ids


for pdf in sorted(folder.glob("*.pdf")):
    print(f"\n--- {pdf.name} ---")
    with open(pdf, "rb") as f:
        r = httpx.post(
            f"{GROBID_URL}/api/processFulltextDocument",
            files={"input": (pdf.name, f, "application/pdf")},
            timeout=60,
        )
    ids = extract_ids(r.text)
    if ids:
        for k, v in ids.items():
            print(f"  {k}: {v}")
    else:
        print("  no identifiers found")
