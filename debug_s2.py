"""
Debug — test Semantic Scholar API call with explicit headers.
Usage: uv run python debug_s2.py
"""
import httpx

url = "https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/ijerph192214858/citations"
params = {"fields": "contexts,intents,isInfluential,citingPaper.title,citingPaper.year", "limit": 3}
headers = {"User-Agent": "MarginaliaResearchTool/0.1"}

print(f"Sending headers: {headers}")
r = httpx.get(url, params=params, headers=headers, timeout=15)
print(f"Status: {r.status_code}")
print(r.text[:500])
