import html
from urllib.parse import quote_plus

import httpx

CREDIBLE_DOMAINS = (
    "nature.com",
    "theconversation.com",
    "quantamagazine.org",
    "arxiv.org",
    "pnas.org",
    "sciencedirect.com",
    "ieee.org",
    "acm.org",
    "biorxiv.org",
    "nytimes.com",
    "theguardian.com",
    "wired.com",
    "technologyreview.com",
)


def _domain_from_url(url: str | None) -> str:
    if not url:
        return ""
    try:
        return url.split("//", 1)[1].split("/", 1)[0].lower()
    except IndexError:
        return ""


def _is_credible(url: str | None) -> bool:
    domain = _domain_from_url(url)
    return any(domain == d or domain.endswith(f".{d}") for d in CREDIBLE_DOMAINS)


def search_pop_sci_mentions(title: str, limit: int = 5) -> list[dict]:
    """Return a small list of likely pop-science / credible coverage for a paper title."""
    if not title or not title.strip():
        return []

    query = quote_plus(title.strip())
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"

    try:
        response = httpx.get(url, timeout=12)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    results: list[dict] = []
    seen: set[str] = set()

    for item in [
        {
            "title": "Abstract",
            "url": data.get("AbstractSource"),
            "snippet": data.get("AbstractText"),
        },
        *(data.get("RelatedTopics") or []),
    ]:
        if not isinstance(item, dict):
            continue

        title_text = item.get("Text") or item.get("Name") or item.get("title") or ""
        url_text = item.get("FirstURL") or item.get("url") or ""
        snippet = item.get("Text") or item.get("snippet") or ""

        if not url_text:
            continue

        clean_title = html.unescape(title_text).strip()
        clean_snippet = html.unescape(snippet).strip()
        source = _domain_from_url(url_text)
        safe_url = url_text.strip()

        if safe_url in seen:
            continue
        seen.add(safe_url)

        results.append(
            {
                "title": clean_title or source or "Web result",
                "url": safe_url,
                "snippet": clean_snippet,
                "source": source,
                "credible": _is_credible(safe_url),
            }
        )

    # sort credible hits first, then keep the likely most useful subset
    results.sort(
        key=lambda x: (0 if x["credible"] else 1, len(x.get("snippet") or "")),
        reverse=True,
    )
    return results[:limit]
