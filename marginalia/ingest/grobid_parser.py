import httpx
from pathlib import Path
from xml.etree import ElementTree as ET

GROBID_URL = "http://localhost:8070"
TEI_NS = "http://www.tei-c.org/ns/1.0"


def parse_with_grobid(pdf_path: Path) -> list[dict]:
    """Call GROBID and return a list of {section, text} dicts."""
    with open(pdf_path, "rb") as f:
        response = httpx.post(
            f"{GROBID_URL}/api/processFulltextDocument",
            files={"input": (pdf_path.name, f, "application/pdf")},
            timeout=60,
        )
    response.raise_for_status()
    return _extract_sections(response.text)


def _extract_sections(tei_xml: str) -> list[dict]:
    root = ET.fromstring(tei_xml)
    sections = []

    for div in root.iter(f"{{{TEI_NS}}}div"):
        head = div.find(f"{{{TEI_NS}}}head")
        section_name = head.text.strip() if head is not None and head.text else "unknown"
        text = " ".join(p.text.strip() for p in div.iter(f"{{{TEI_NS}}}p") if p.text)
        if text:
            sections.append({"section": section_name, "text": text})

    return sections
