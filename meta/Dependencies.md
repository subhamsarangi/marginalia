# Marginalia — Dependency Map

## Core orchestration
- `langchain` (1.x) — retrieval chains, memory
- `langchain-core` — shared abstractions (pinned in lockstep with the above)
- `langchain-google-genai` — Google Gemini chat client (replaces GitHub Models / langchain-openai)
- `langchain-community` — misc loaders/integrations glue
- `langchain-text-splitters` — section-aware chunking utilities

**LLM provider: Google AI Studio (Gemini).** GitHub Models retired, switched to Google AI Studio free tier. Model: `gemini-3.8-flash`. Auth via `GOOGLE_API_KEY`.

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

## Discipline Classification
Deterministic pass uses three signals in priority order:
1. arXiv ID pattern (`NNNN.NNNNN`) found in text → STEM
2. Section-header overlap: ≥3 matches against known IMRaD headers → STEM, ≥2 matches against humanities headers → humanities
3. Citation style: numbered refs `[1]` → STEM, author-date `(Smith, 2020)` → humanities

LLM fallback is invoked only when deterministic pass returns `ambiguous`. Result is cached as `discipline`, `discipline_method`, and `discipline_confidence` fields in each chunk's Qdrant metadata — no separate cache store needed, classified once at ingestion.

### Subtype classification
Two-field flat schema — subtypes are nullable depending on top-level discipline:
- `stem_subtype`: `empirical` | `review` | `unknown` | `null`
- `humanities_subtype`: `argumentative` | `historical` | `interpretive` | `unknown` | `null`

**Why these subtypes earn their place (each maps to a different processing path):**

`stem_subtype`:
- `empirical` → GROBID IMRaD parsing trusted at full confidence, clean Methods/Results boundaries expected
- `review` → GROBID still runs but section labels won't map to IMRaD cleanly; flag for Docling fallback heuristic check rather than trusting GROBID structure blindly
- `unknown` → route conservatively through Docling; guessing wrong on IMRaD assumptions is worse than a generic fallback

`humanities_subtype` (axis is rhetorical structure, not evidence structure):
- `argumentative` → linear thesis-building; chunk by argument/section headers; footnotes carry citation weight
- `historical` → may contain embedded primary-source quotations, timelines, tables/demographic data; flag for Docling's table handling
- `interpretive` → quote-dense, may reference an external work (novel, film, artwork) not in the paper itself; matters for citation/quote extraction downstream
- `unknown` → catch-all

**Detection strategy:**
- Deterministic subtype heuristics run first (no LLM cost), in priority order:
  1. Title check — `review`, `narrative review`, `systematic review`, `meta-analysis`, `scoping review` in title → `review`
  2. Methods section content — empirical signals (`n=`, `p<`, `sample size`, `we recruit`, etc.) vs synthesis signals (`we review`, `we search`, `PubMed`, `included studies`, etc.) → `empirical` or `review`
  3. Header partial match — `method`/`result` substrings in headers (covers `Materials and Methods`, `Overall Results`, etc.)
- LLM subtype classification only happens inside the existing ambiguous fallback call — no extra LLM pass
- Subtype stored alongside discipline in Qdrant chunk metadata
- Title extracted from GROBID TEI-XML `titleStmt/title` and stored as `_title` section (used for classification, not chunked into Qdrant)


- Python 3.12 (broad compatibility across the langchain 1.x line, which supports 3.10–3.14).
- GROBID is **not** a pip package — it runs as a separate Java service (Docker image `lfoppiano/grobid`), called over HTTP from the ingestion pipeline. `pymupdf4llm` and `docling` are Python-installable and act as fallbacks when GROBID isn't reachable or underperforms on non-IMRaD (humanities) papers.