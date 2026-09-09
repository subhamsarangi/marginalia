# Marginalia — Dependency Map

## Core orchestration
- `langchain` (1.x) — retrieval chains, memory
- `langchain-core` — shared abstractions (pinned in lockstep with the above)
- `langchain-openai` (1.6.x) — Azure OpenAI / OpenAI-compatible chat + embeddings client
- `langchain-community` — misc loaders/integrations glue
- `langchain-text-splitters` — section-aware chunking utilities

## Vector store
- `langchain-qdrant` (1.1.x) — LangChain ↔ Qdrant integration
- `qdrant-client` — Qdrant Cloud free-tier client

**Decision: Qdrant Cloud over Azure AI Search.** Qdrant free tier gives 1GB RAM / 4GB disk (~1M vectors @768d) on a dedicated node. Azure AI Search F0 is capped at 50MB storage across 3 indexes on shared/multi-tenant compute — too tight for 8-10 papers plus rubric/enrichment metadata. Tradeoff: Qdrant free clusters auto-suspend after 1 week idle, deleted after 4 weeks — mitigate with a weekly GitHub Actions cron ping, or just reactivate before a demo.

## PDF ingestion & section detection
- `pypdf` — lightweight fallback text extraction
- `pymupdf` (fitz) / `pymupdf4llm` — fast, pure-Python layout extraction, last-resort fallback
- **GROBID** (self-hosted via Docker, free) — purpose-built ML parser for academic PDFs; extracts structured TEI-XML with real section boundaries (title, abstract, methods, results, discussion, references). Field standard — backs the Semantic Scholar/S2ORC corpus. Best for STEM/IMRaD-structured papers.
- **Docling** (IBM, `docling` on PyPI) — genre-agnostic layout + table structure parser, stronger fallback for humanities papers that don't follow IMRaD structure or where GROBID's section model doesn't fit.

**Fallback parse chain:** GROBID (primary, STEM/IMRaD) → pymupdf4llm (fast first-pass fallback) → Docling (deep fallback when pymupdf4llm output is degenerate). Degeneracy is detected by three heuristics: total text < 500 chars, fewer than 2 sections detected, or >40% of lines are single characters (garbled OCR).

Chunking is two separate problems: **layout detection** (where does Methods start — GROBID/Docling's job) and **text splitting** (how do I size a long section into embeddable chunks — `langchain-text-splitters`' job, scoped down from "detect structure" to "size structure"). `RecursiveCharacterTextSplitter` still runs downstream of GROBID/Docling output for oversized sections.

## API layer
- `fastapi` — backend framework
- `uvicorn[standard]` — ASGI server
- `python-multipart` — file upload handling (PDF uploads)
- `sse-starlette` — streaming responses over SSE

## Config / secrets
- `python-dotenv` — local `.env` loading
- `pydantic-settings` — typed config management

## External enrichment
- `httpx` — async HTTP client for Semantic Scholar API + web search calls
- `tenacity` — retry/backoff for flaky external API calls

## Eval
- `ragas` — RAG evaluation (faithfulness, relevance scoring)
- `pandas` — eval result tables

## Guardrails / infra
- `slowapi` — rate limiting for FastAPI
- `cachetools` — in-memory response caching (swap for Redis if scaling later)

## Dev tooling
- `pytest` — testing
- `ruff` — lint + format (fast, single tool replaces flake8/black/isort)

---

## Notes
- Python 3.12 recommended (broad compatibility across the langchain 1.x line, which supports 3.10–3.14).
- Azure OpenAI access via GitHub Models free tier uses the OpenAI-compatible endpoint, so `langchain-openai`'s `AzureChatOpenAI`/`ChatOpenAI` client works by pointing `base_url` at the GitHub Models endpoint — no separate Azure SDK needed for the free-tier path.
- If moving to a paid Azure OpenAI resource later, add `azure-identity` for managed auth.
- GROBID is **not** a pip package — it runs as a separate Java service (Docker image `lfoppiano/grobid`), called over HTTP from the ingestion pipeline. `pymupdf4llm` and `docling` are Python-installable and act as fallbacks when GROBID isn't reachable or underperforms on non-IMRaD (humanities) papers.