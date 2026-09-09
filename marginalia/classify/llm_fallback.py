import os
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


def classify_with_llm(sections: list[dict]) -> dict:
    """LLM fallback for ambiguous papers. Returns same shape as deterministic.classify()."""
    section_names = [s["section"] for s in sections]
    sample_text = " ".join(s["text"][:300] for s in sections[:3])

    prompt = f"""You are classifying an academic paper as either STEM or humanities.

Section headers: {section_names}
Text sample: {sample_text}

Reply with a JSON object only, no markdown:
{{"discipline": "stem" or "humanities", "confidence": 0.0-1.0, "reason": "one sentence"}}"""

    response = _get_llm().invoke([HumanMessage(content=prompt)])
    import json
    result = json.loads(response.content)
    return {
        "discipline": result["discipline"],
        "method": "llm",
        "confidence": result["confidence"],
        "reason": result.get("reason", ""),
    }
