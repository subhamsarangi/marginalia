import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0,
        )
    return _llm


STEM_PROMPT = """You are extracting structured signals from a STEM academic paper.
Do NOT make quality judgments — only extract what is present or absent as factual flags.

Paper text (truncated):
{text}

Reply with a JSON object only, no markdown:
{{
  "sample_size": <integer or null>,
  "has_control_group": <true/false/null>,
  "reports_effect_size": <true/false>,
  "reports_p_value_only": <true/false>,
  "has_limitations_section": <true/false>,
  "funding_disclosed": <true/false/null>,
  "conflict_of_interest_disclosed": <true/false/null>,
  "is_review": <true/false>
}}"""

HUMANITIES_PROMPT = """You are extracting structured signals from a humanities academic paper.
Do NOT make quality judgments — only extract what is present or absent as factual flags.

Paper text (truncated):
{text}

Reply with a JSON object only, no markdown:
{{
  "engages_existing_scholarship": <true/false>,
  "primary_source_ratio": "high" | "medium" | "low" | null,
  "acknowledges_counterarguments": <true/false>,
  "scope_evidence_proportionate": <true/false/null>,
  "has_footnotes": <true/false>
}}"""


def _parse_response(response) -> dict:
    content = response.content
    if isinstance(content, list):
        content = "".join(c if isinstance(c, str) else c.get("text", "") for c in content)
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(content)


def extract_rubric(sections: list[dict], discipline: str, stem_subtype: str | None = None) -> dict:
    """Extract rubric signals from paper sections. Returns a dict of flags."""
    # Use first 6 sections to stay within token limits
    text = "\n\n".join(
        f"[{s['section']}]\n{s['text']}"
        for s in sections
        if not s["section"].startswith("_")
    )[:8000]

    if discipline == "stem":
        prompt = STEM_PROMPT.format(text=text)
    else:
        prompt = HUMANITIES_PROMPT.format(text=text)

    response = _get_llm().invoke([HumanMessage(content=prompt)])
    rubric = _parse_response(response)
    rubric["discipline"] = discipline
    rubric["stem_subtype"] = stem_subtype
    return rubric
