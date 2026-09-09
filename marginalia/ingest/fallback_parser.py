import pymupdf4llm
from pathlib import Path


def parse_with_pymupdf(pdf_path: Path) -> list[dict]:
    md_text = pymupdf4llm.to_markdown(str(pdf_path))
    sections = _split_by_headers(md_text)
    if _is_degenerate(md_text, sections):
        return None  # signal caller to fall back to Docling
    return sections


def _split_by_headers(md_text: str) -> list[dict]:
    sections = []
    current_section = "unknown"
    buffer = []

    for line in md_text.splitlines():
        if line.startswith("#"):
            if buffer:
                sections.append({"section": current_section, "text": " ".join(buffer).strip()})
                buffer = []
            current_section = line.lstrip("#").strip()
        else:
            if line.strip():
                buffer.append(line.strip())

    if buffer:
        sections.append({"section": current_section, "text": " ".join(buffer).strip()})

    return sections


def _is_degenerate(md_text: str, sections: list[dict]) -> bool:
    if len(md_text.strip()) < 500:
        return True
    if len(sections) < 2:
        return True
    lines = [l for l in md_text.splitlines() if l.strip()]
    single_char_ratio = sum(1 for l in lines if len(l.strip()) == 1) / max(len(lines), 1)
    if single_char_ratio > 0.4:
        return True
    return False
