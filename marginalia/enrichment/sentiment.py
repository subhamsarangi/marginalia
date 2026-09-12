import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from langchain_google_genai.chat_models import GoogleRateLimitError

INPUT_COST_PER_M = 0.75
OUTPUT_COST_PER_M = 3.75

_llm = None
_openai_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0,
        )
    return _llm


def _get_openai_llm():
    global _openai_llm
    if _openai_llm is None:
        _openai_llm = ChatOpenAI(
            model="gpt-5.4-nano",
            api_key=os.environ["OPENAI_API_KEY"],
            temperature=0,
        )
    return _openai_llm


def _invoke(prompt: str):
    try:
        return _get_llm().invoke([HumanMessage(content=prompt)])
    except GoogleRateLimitError:
        print("  [LLM] Google quota exhausted; switching to OpenAI fallback.")
        try:
            response = _get_openai_llm().invoke([HumanMessage(content=prompt)])
            print("  [LLM] OpenAI fallback succeeded.")
            return response
        except Exception as fallback_exc:
            print("  [LLM] OpenAI fallback failed.")
            raise RuntimeError(
                "Gemini quota exhausted and OpenAI fallback also failed."
            ) from fallback_exc


PROMPT = """Classify the sentiment of each citation context sentence as approving, critical, or neutral.
A sentence is approving if it endorses, builds on, or positively references the cited work.
A sentence is critical if it challenges, contradicts, or identifies limitations of the cited work.
Otherwise it is neutral.

Contexts (one per line):
{contexts}

Reply with a JSON array only, no markdown, one object per context in the same order:
[{{"sentiment": "approving"|"critical"|"neutral"}}]"""


def classify_sentiments(contexts: list[str]) -> tuple[list[str], dict]:
    """
    Returns (list of sentiments, usage dict).
    Sentiments are in the same order as input contexts.
    """
    if not contexts:
        return [], {
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": 0.0,
        }

    prompt = PROMPT.format(
        contexts="\n".join(f"{i+1}. {c}" for i, c in enumerate(contexts))
    )
    try:
        response = _invoke(prompt)
    except GoogleRateLimitError as exc:
        raise RuntimeError(
            "Gemini quota exhausted; sentiment enrichment skipped."
        ) from exc

    content = response.content
    if isinstance(content, list):
        content = "".join(
            c if isinstance(c, str) else c.get("text", "") for c in content
        )
    content = (
        content.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    results = json.loads(content)
    sentiments = [r["sentiment"] for r in results]

    usage_meta = response.usage_metadata or {}
    input_tokens = usage_meta.get("input_tokens", 0)
    output_tokens = usage_meta.get("output_tokens", 0)
    thinking_tokens = usage_meta.get("thinking_tokens", 0) or 0
    cost = (input_tokens / 1_000_000 * INPUT_COST_PER_M) + (
        (output_tokens + thinking_tokens) / 1_000_000 * OUTPUT_COST_PER_M
    )

    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "cost_usd": round(cost, 6),
    }
    return sentiments, usage
