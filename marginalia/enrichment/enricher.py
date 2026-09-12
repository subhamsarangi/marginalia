from marginalia.enrichment.semantic_scholar import resolve_s2_id, get_citations
from marginalia.enrichment.sentiment import classify_sentiments
from marginalia.enrichment.web_search import search_pop_sci_mentions

MAX_CONTEXTS = 10


def enrich_paper(
    paper_id: str,
    title: str = None,
    arxiv_id: str = None,
    doi: str = None,
    acl_id: str = None,
) -> tuple[dict, dict]:
    """
    Fetch citations from Semantic Scholar, classify sentiment with Gemini.
    Returns (enrichment dict, usage dict).
    """
    s2_id = resolve_s2_id(title=title, arxiv_id=arxiv_id, doi=doi, acl_id=acl_id)
    if not s2_id:
        return {
            "paper_id": paper_id,
            "s2_id": None,
            "citations": [],
            "error": "unresolved",
        }, {
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": 0.0,
        }

    try:
        raw_citations = get_citations(s2_id)
    except Exception as e:
        print(f"  [S2] citations fetch failed: {e}")
        return {
            "paper_id": paper_id,
            "s2_id": s2_id,
            "citations": [],
            "error": str(e),
        }, {
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": 0.0,
        }

    # Sort: influential citations first, then others
    raw_citations.sort(key=lambda c: not c.get("isInfluential", False))

    citations = []
    all_contexts = []
    context_index = []
    context_budget = MAX_CONTEXTS

    for i, c in enumerate(raw_citations):
        # Skip citations with no context — no point sending to Gemini
        contexts = [ctx for ctx in (c.get("contexts") or []) if ctx.strip()]

        # Cap total contexts sent to Gemini
        if context_budget > 0 and contexts:
            selected = contexts[:context_budget]
            context_budget -= len(selected)
        else:
            selected = []

        for ctx in selected:
            all_contexts.append(ctx)
            context_index.append(i)

        citations.append(
            {
                "citing_title": c.get("citingPaper", {}).get("title"),
                "citing_year": c.get("citingPaper", {}).get("year"),
                "intents": c.get("intents", []),
                "is_influential": c.get("isInfluential", False),
                "contexts": contexts,
                "sentiments": [],
            }
        )

    print(
        f"  [LLM batch] citation_contexts={len(all_contexts)} total_chars={sum(len(ctx) for ctx in all_contexts)}"
    )
    try:
        sentiments, usage = classify_sentiments(all_contexts)
    except RuntimeError as exc:
        print(f"  [LLM] {exc}")
        return {
            "paper_id": paper_id,
            "s2_id": s2_id,
            "citation_count": len(citations),
            "citations": citations,
            "error": str(exc),
        }, {
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": 0.0,
        }

    for flat_idx, sentiment in enumerate(sentiments):
        cit_idx = context_index[flat_idx]
        citations[cit_idx]["sentiments"].append(sentiment)

    web_mentions = []
    if title:
        try:
            web_mentions = search_pop_sci_mentions(title, limit=5)
        except Exception as exc:
            print(f"  [Web] search failed: {exc}")
            web_mentions = []

    enrichment = {
        "paper_id": paper_id,
        "s2_id": s2_id,
        "citation_count": len(citations),
        "citations": citations,
        "web_mentions": web_mentions,
    }
    return enrichment, usage
