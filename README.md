# Marginalia

A research-paper RAG assistant with discipline-aware answers, in-paper rubric extraction, and external reception enrichment.

**Repo:** https://github.com/subhamsarangi/marginalia.git

## Stack
- LangChain 1.x + LangChain-Google-GenAI (Google AI Studio free tier, Gemini)
- Qdrant Cloud (free tier) — vector store
- GROBID — section-aware PDF parsing for STEM papers
- Docling / pymupdf4llm — fallback parser for humanities papers
- FastAPI + Uvicorn — API layer
- Semantic Scholar API — external citation enrichment

## Local Setup
```bash
uv venv && uv sync --dev
cp .env.example .env  # fill in your keys
```

## Status
Work in progress.
