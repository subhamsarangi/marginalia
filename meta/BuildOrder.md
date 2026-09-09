# Marginalia — Build Order

A research-paper RAG assistant with discipline-aware answers, in-paper rubric extraction, and external reception enrichment.

---

## 1. Repo + Env Setup
- [x] Create GitHub repo, initialize with `.gitignore`, README stub
- [x] Set up Python venv, install core deps (FastAPI, LangChain, etc.)
- [x] Get GitHub Models token for free Azure OpenAI access
- [x] Set up `.env` for secrets (API keys, tokens)

## 2. Corpus
- [x] Source 8–10 open-access papers
- [x] Mix STEM (arXiv) with humanities (JSTOR open / Project MUSE open-access / public philosophy papers)
- [x] Store raw PDFs in a `corpus/` directory

## 3. Ingest + Section-Aware Chunking
- [x] Stand up GROBID via Docker (`lfoppiano/grobid`), called over HTTP — parses STEM/IMRaD papers into structured TEI-XML with real section boundaries (abstract/methods/results/discussion)
- [x] Add Docling (or pymupdf4llm) as fallback parser for humanities papers that don't fit IMRaD structure, or when GROBID underperforms/fails
  - pymupdf4llm is the fast first pass; Docling is the deep fallback when pymupdf4llm output is degenerate (text < 500 chars, < 2 sections, or >40% single-char lines)
- [ ] Run `RecursiveCharacterTextSplitter` (langchain-text-splitters) downstream, only on oversized sections — its job shrinks from "detect structure" to "size structure" now that GROBID/Docling do the actual section detection
- [ ] Attach metadata to each chunk (paper ID, section name, page number, parser used)
- [ ] Push chunks + embeddings to Qdrant Cloud (chosen over Azure AI Search — see dependencies.md for the tradeoff)
- [ ] Set up a weekly keep-alive ping (GitHub Actions cron) so the free Qdrant cluster doesn't auto-suspend from inactivity

## 4. Discipline Classification
- [ ] Deterministic pass: arXiv category tag, journal/venue name, citation style, section-header structure
- [ ] LLM fallback for ambiguous or metadata-less documents, with confidence score
- [ ] Cache discipline label per paper (classify once at ingestion, not per query)

## 5. In-Paper Rubric Extraction
- [ ] Structured LLM extraction pass per paper (JSON output, not conversational)
- [ ] STEM branch: sample size, control/comparison group, effect size vs. p-value only, limitations section present, funding/conflict of interest disclosed
- [ ] Humanities branch: engagement with existing scholarship, primary vs. secondary source ratio, counterargument acknowledgment, scope-to-evidence proportionality
- [ ] Store as flags/signals, not quality verdicts

## 6. External Enrichment (async, per-paper)
- [ ] Primary source: Semantic Scholar API for citation context and sentiment (approving vs. critical citations)
- [ ] Secondary source: web search for pop-sci coverage (Nature News, The Conversation, Quanta) and social/discourse signals, with credibility filtering
- [ ] Every external claim stored with a source link — no summarizing without citation
- [ ] Run once per paper (on ingestion or on-demand), cache the result

## 7. RAG Core + Answer-Style Prompt
- [ ] Retrieval chain: query → retrieve chunks → prompt LLM → cited answer
- [ ] Discipline-aware answer shaping (methodology callouts for empirical papers, argument/framing callouts for humanities)
- [ ] Preserve source hedging language (don't flatten "suggests" into "proves")
- [ ] Clear separation in output: "within the paper" vs. "external reception"
- [ ] Cross-paper synthesis with contradictions flagged explicitly, not blended

## 8. API Layer
- [ ] FastAPI backend
- [ ] Streaming responses
- [ ] Endpoints: `/ask`, `/rubric/{paper_id}`, `/enrichment/{paper_id}` (check external commentary)

## 9. Guardrails
- [ ] Rate limiting per user/IP
- [ ] Response caching for repeated/similar queries
- [ ] Prompt-injection check on retrieved chunk content

## 10. Frontend
- [ ] Simple UI (Streamlit or minimal React)
- [ ] Chunk provenance view (show retrieved source alongside answer)
- [ ] Rubric flags panel (strengths/weaknesses signals)
- [ ] External signals panel (citation sentiment, pop-sci/social mentions)

## 11. Eval
- [ ] Test question set covering:
  - [ ] Retrieval accuracy
  - [ ] Hedging fidelity (does the answer preserve the source's epistemic confidence)
  - [ ] Rubric correctness (spot-check extracted flags against manual read)
  - [ ] Citation grounding for external claims (no unsourced assertions)
- [ ] Score via RAGAS or manual scoring, save results to repo

## 12. Deploy
- [ ] Backend → Azure App Service (F1 free tier)
- [ ] Frontend → Azure Static Web Apps (free tier)

## 13. Logging
- [ ] Azure Application Insights (free tier) for request/error tracking

## 14. README
- [ ] Architecture diagram
- [ ] Cost breakdown ($0 target)
- [ ] Local run instructions