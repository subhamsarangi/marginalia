"""
Deterministic discipline + subtype classifier.
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

# Partial match keywords — covers 'Materials and Methods', 'Overall Results', etc.
IMRAD_CORE_KEYWORDS = {"method", "result"}
REVIEW_KEYWORDS = {"review", "literature", "survey", "synthesis", "overview"}
REVIEW_TITLE_KEYWORDS = {"review", "narrative review", "systematic review",
                         "meta-analysis", "meta analysis", "scoping review", "overview"}

# Empirical content signals in methods text
EMPIRICAL_SIGNALS = re.compile(
    r"\bn\s*=\s*\d+|p\s*[<=>]\s*0\.\d+|sample size|data collect|we recruit|we enroll|"
    r"randomized|cohort|participants|subjects|specimens|assay|sequenc",
    re.IGNORECASE
)
SYNTHESIS_SIGNALS = re.compile(
    r"we review|we search|we compar|we analyz|we synthesiz|pubmed|scopus|web of science|"
    r"included studies|eligible studies|search strateg",
    re.IGNORECASE
)

ARXIV_PATTERN = re.compile(r"\b\d{4}\.\d{4,5}\b")
NUMBERED_REF = re.compile(r"\[\d+\]")
AUTHOR_DATE = re.compile(r"\([A-Z][a-z]+,?\s+\d{4}\)")
FOOTNOTE = re.compile(r"\^\d+|\[\^\d+\]|^\d+\s+", re.MULTILINE)
BLOCK_QUOTE = re.compile(r'"[^"]{80,}"|\u201c[^\u201d]{80,}\u201d')


def _stem_subtype(headers: set, sections: list[dict]) -> str:
    # 1. Check title first
    title = next((s["text"].lower() for s in sections if s["section"] == "_title"), "")
    if any(k in title for k in REVIEW_TITLE_KEYWORDS):
        return "review"

    # 2. Check methods section content
    methods_text = " ".join(
        s["text"] for s in sections
        if any(k in s["section"].lower() for k in IMRAD_CORE_KEYWORDS)
    )
    if methods_text:
        empirical_hits = len(EMPIRICAL_SIGNALS.findall(methods_text))
        synthesis_hits = len(SYNTHESIS_SIGNALS.findall(methods_text))
        if empirical_hits > synthesis_hits:
            return "empirical"
        if synthesis_hits > 0:
            return "review"

    # 3. Fall back to header partial match
    imrad_hits = sum(1 for h in headers for k in IMRAD_CORE_KEYWORDS if k in h)
    if imrad_hits >= 2:
        return "empirical"
    if any(k in h for h in headers for k in REVIEW_KEYWORDS):
        return "review"

    return "unknown"


def _humanities_subtype(headers: set, raw_text: str) -> str:
    footnote_count = len(FOOTNOTE.findall(raw_text))
    quote_count = len(BLOCK_QUOTE.findall(raw_text))
    historical_keywords = {"archive", "archival", "manuscript", "census", "chronicle",
                           "primary source", "historical", "period", "century"}
    if any(k in raw_text.lower() for k in historical_keywords):
        return "historical"
    if quote_count > 5:
        return "interpretive"
    if footnote_count > 10:
        return "argumentative"
    return "unknown"


def classify(sections: list[dict], raw_text: str = "") -> dict:
    """
    Returns {"discipline", "stem_subtype", "humanities_subtype", "method", "confidence"}
    """
    headers = {s["section"].lower().strip() for s in sections}
    stem_hits = headers & STEM_SECTIONS
    hum_hits = headers & HUMANITIES_SECTIONS

    # 1. arXiv ID in text
    if ARXIV_PATTERN.search(raw_text):
        return {
            "discipline": "stem",
            "stem_subtype": _stem_subtype(headers, sections),
            "humanities_subtype": None,
            "method": "arxiv_id",
            "confidence": 0.95,
        }

    # 2. Section-header structure
    if len(stem_hits) >= 3:
        return {
            "discipline": "stem",
            "stem_subtype": _stem_subtype(headers, sections),
            "humanities_subtype": None,
            "method": "section_headers",
            "confidence": 0.85,
        }
    if len(hum_hits) >= 2:
        return {
            "discipline": "humanities",
            "stem_subtype": None,
            "humanities_subtype": _humanities_subtype(headers, raw_text),
            "method": "section_headers",
            "confidence": 0.80,
        }

    # 3. Citation style
    numbered = len(NUMBERED_REF.findall(raw_text))
    author_date = len(AUTHOR_DATE.findall(raw_text))

    if numbered > author_date and numbered > 5:
        return {
            "discipline": "stem",
            "stem_subtype": _stem_subtype(headers, sections),
            "humanities_subtype": None,
            "method": "citation_style",
            "confidence": 0.70,
        }
    if author_date > numbered and author_date > 5:
        return {
            "discipline": "humanities",
            "stem_subtype": None,
            "humanities_subtype": _humanities_subtype(headers, raw_text),
            "method": "citation_style",
            "confidence": 0.70,
        }

    return {
        "discipline": "ambiguous",
        "stem_subtype": None,
        "humanities_subtype": None,
        "method": "none",
        "confidence": 0.0,
    }
