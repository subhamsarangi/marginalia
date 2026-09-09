from pathlib import Path
from docling.document_converter import DocumentConverter


_converter = DocumentConverter()


def parse_with_docling(pdf_path: Path) -> list[dict]:
    result = _converter.convert(str(pdf_path))
    md_text = result.document.export_to_markdown()
    return _split_by_headers(md_text)


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
