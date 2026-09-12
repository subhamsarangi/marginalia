import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

BASE_URL = "https://api.semanticscholar.org/graph/v1"
CITATION_FIELDS = "contexts,intents,isInfluential,citingPaper.title,citingPaper.year"


def _headers() -> dict:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"User-Agent": "MarginaliaResearchTool/0.1"}
    if key:
        headers["x-api-key"] = key
    return headers


def _is_retryable(exc) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code not in (403, 404)
    return True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
       retry=retry_if_exception(_is_retryable))
def _get(url: str, params: dict = None) -> dict:
    r = httpx.get(url, params=params, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def resolve_s2_id(title: str = None, arxiv_id: str = None,
                  doi: str = None, acl_id: str = None) -> str | None:
    """Resolve a paper to a Semantic Scholar paper ID using fallback chain."""
    if arxiv_id:
        return f"arXiv:{arxiv_id}"
    if doi:
        return f"DOI:{doi}"
    if acl_id:
        return f"ACL:{acl_id}"
    if title:
        try:
            data = _get(f"{BASE_URL}/paper/search", params={"query": title, "limit": 1})
            results = data.get("data", [])
            if results:
                return results[0]["paperId"]
        except Exception as e:
            print(f"  [S2] title search failed: {e}")
    return None


def get_citations(s2_id: str, limit: int = 50) -> list[dict]:
    """Fetch citations for a paper. Returns list of raw citation dicts."""
    data = _get(
        f"{BASE_URL}/paper/{s2_id}/citations",
        params={"fields": CITATION_FIELDS, "limit": limit},
    )
    return data.get("data", [])
