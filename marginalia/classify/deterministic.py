"""
Deterministic discipline classifier.
Signal priority:
  1. arXiv category tag in metadata (if present)
  2. IMRaD section-header structure
  3. Citation style (numbered vs author-date)
Returns: "stem" | "humanities" | "ambiguous"
"""
import re

STEM_SECTIONS = {"abstract", "introduction", "methods", "methodology", "results",
                 "discussion", "conclusion", "related work", "experiments"}
HUMANITIES_SECTIONS = {"preface", "foreword", "argument", "critique", "interpretation",
                       "analysis", "bibliography", "notes", "acknowledgements"}

ARXIV_PATTERN = re.compile(r"\b\d{4}\.\d{4,5}\b")  # arXiv ID pattern e.g. 2301.12345
NUMBERED_REF = re.compile(r"\[\d+\]")               # [1], [2] — STEM citation style
AUTHOR_DATE = re.compile(r"\([A-Z][a-z]+,?\s+\d{4}\)")  # (Smith, 2020) — humanities


def classify(sections: list[dict], raw_text: str = "") -> dict:
    """
    Returns {"discipline": "stem"|"humanities"|"ambiguous", "method": str, "confidence": float}
    """
    # 1. arXiv ID in text
    if ARXIV_PATTERN.search(raw_text):
        return {"discipline": "stem", "method": "arxiv_id", "confidence": 0.95}

    # 2. Section-header structure
    headers = {s["section"].lower().strip() for s in sections}
    stem_hits = headers & STEM_SECTIONS
    hum_hits = headers & HUMANITIES_SECTIONS

    if len(stem_hits) >= 3:
        return {"discipline": "stem", "method": "section_headers", "confidence": 0.85}
    if len(hum_hits) >= 2:
        return {"discipline": "humanities", "method": "section_headers", "confidence": 0.80}

    # 3. Citation style
    numbered = len(NUMBERED_REF.findall(raw_text))
    author_date = len(AUTHOR_DATE.findall(raw_text))

    if numbered > author_date and numbered > 5:
        return {"discipline": "stem", "method": "citation_style", "confidence": 0.70}
    if author_date > numbered and author_date > 5:
        return {"discipline": "humanities", "method": "citation_style", "confidence": 0.70}

    return {"discipline": "ambiguous", "method": "none", "confidence": 0.0}
