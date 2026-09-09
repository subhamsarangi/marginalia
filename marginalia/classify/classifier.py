from marginalia.classify.deterministic import classify
from marginalia.classify.llm_fallback import classify_with_llm


def get_discipline(sections: list[dict], raw_text: str = "") -> dict:
    result = classify(sections, raw_text)
    if result["discipline"] == "ambiguous":
        result = classify_with_llm(sections)
    return result
