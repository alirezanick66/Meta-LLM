# Copilot Instructions for Meta-LLM

## Language & Formatting Rules

- Write all Persian text in short, separate paragraphs.
- Put all English words and technical terms inside backticks.
- Never mix Persian and English in the same sentence.
- Do not use horizontal rules (---) to separate sections.
- Use emojis for better readability.

## Code Sending Rules

- Never send any code or file without my explicit approval.
- If only a small part of the code has changed, send only that part with a few lines before and after it. Never resend the entire file.

## Comments & Documentation

- Only add comments for complex logic or public functions.
- Use docstrings for all functions.

## Agent & PR Rules

- Never open a pull request or apply any code changes automatically.
- Always wait for my explicit approval before taking any action.

## Project Overview

Persian-language RAG (Retrieval-Augmented Generation) Q&A system for urban planning and civil engineering documents. FastAPI backend + React 18 frontend, targeting ~1000-page Markdown corpus (~3000–4000 chunks).

## Architecture

### Data Flow

```
User Query → Persian Normalization → Parallel BM25 + Vector Retrieval (Top-20 each)
→ Reciprocal Rank Fusion (Top-20) → Final Top-5 → Prompt Builder → LLM Orchestrator
(Primary: Groq llama-3.3-70b-versatile, Fallback: Gemini gemini-2.0-flash-exp) → Answer + Sources
```

### Key Directories

- `backend/app/api/` – FastAPI routes, dependency injection (Singleton services), exception handlers
- `backend/app/services/retrieval/` – BM25 indexer, vector retriever, hybrid retriever with RRF
- `backend/app/services/vector/` – QdrantManager, QdrantIndexer
- `backend/app/services/llm/` – GroqClient, GeminiClient, LLMOrchestrator (primary/fallback logic)
- `backend/app/services/document/` – MarkdownExtractor, WordExtractor, PersianNormalizer, MarkdownChunker
- `backend/app/schemas/` – base_schemas, api_schemas, chat_schemas, chunk_schemas, llm_schemas, retrieval_schemas
- `backend/app/utils/logging_config.py` – Loguru-based logger with Persian text support (bidi + arabic_reshaper)
- `backend/app/core/config.py` – All settings via `pydantic_settings.BaseSettings`; reads from `.env`
- `backend/data/documents/` – Source Markdown files; `backend/data/storage/bm25_cache/` – BM25 pickle files
- `scripts/` – Test scripts: `test_api.py`, `test_retrieval.py`, `test_rag_pipline.py`, etc.
- `frontend/src/components/` – ChatInterface, Message, InputBox, MessageActions, SkeletonMessage, ScrollToBottom, SourceCards, SourceModal

## Developer Workflows

### Backend Setup

```bash
pip install -r requirements.txt
docker-compose up -d          # PostgreSQL, Qdrant, Redis
alembic upgrade head          # apply migrations
uvicorn backend.app.main:app --reload   # API at http://localhost:8000
```

### Frontend Setup

```bash
cd frontend && npm install
npm run dev    # http://localhost:3000
```

### Test Scripts (run from repo root)

```bash
python scripts/test_api.py          # 6 API tests (health, stats, chat)
python scripts/test_retrieval.py    # BM25 + vector retrieval
python scripts/test_rag_pipline.py  # full pipeline (note: filename has a typo)
python scripts/test_full_indexing.py  # index a document end-to-end
```

### Reset All Data

```bash
docker-compose down -v && docker-compose up -d && alembic upgrade head
```

## Key Patterns & Conventions

### Logging

Use `log_message(LG.<Category>, "message", LogLevel.<LEVEL>)` — never use `print()` or raw `logger` directly. Categories: `LG.API`, `LG.Database`, `LG.DataProcessing`, `LG.Retrieval`, `LG.LLM`.

### Dependency Injection (Singletons)

Heavy services (HybridRetriever, LLMOrchestrator) are injected as singletons via `backend/app/api/dependencies.py`. Use `Depends(get_hybrid_retriever)` and `Depends(get_llm_orchestrator)` in route handlers. Never instantiate these inside endpoints.

### Async-safe Blocking Calls

Wrap all synchronous CPU-bound operations inside async endpoints with `run_in_threadpool`:

```python
results = await run_in_threadpool(retriever.search, query)
```

### Pydantic V2

All schemas use Pydantic V2 syntax (`model_config`, `computed_field`). Settings use `pydantic_settings.BaseSettings`.

### Persian Text

Always normalize queries with `PersianNormalizer` before retrieval. The custom normalizer uses `str.translate` (no Hazm dependency). Log messages use `arabic_reshaper` + `bidi` for correct terminal display.

### Retrieval Schemas

All retrieval-related constants are defined in `backend/app/schemas/retrieval_schemas.py`:

```python
class RetrievalMethod   # BM25, VECTOR
class ResultKeys        # CHUNK_ID, SCORE, RETRIEVAL_METHOD, METADATA, CONTENT
class RRFKeys           # RRF_SCORE, BM25_SCORE, VECTOR_SCORE, BM25_RANK, VECTOR_RANK
class RRFStats          # BOTH, ONLY_BM25, ONLY_VECTOR
```

### Qdrant Point IDs

SHA-256(chunk_id)[:8] converted to int. Payload includes: `chunk_id`, `document_id`, `source`, `hierarchy`. Batch insert size: 100.

### BM25 Storage

BM25 index and chunk_id mapping stored as pickles in `backend/data/storage/bm25_cache/`. Only chunk_ids are kept in memory; content is fetched from PostgreSQL via bulk queries when needed.

### Frontend

RTL layout (Persian); Tailwind utility classes; `useTypingEffect` hook for character-by-character response rendering. Message colors: user `#fff6d9`, bot transparent. Send button `#ffc414`. Font: `mikhak` (local).

## External Dependencies

- **Groq API** (`GROQ_API_KEY`) – primary LLM (llama-3.3-70b-versatile)
- **Gemini API** (`GEMINI_API_KEY`) – fallback LLM (gemini-2.0-flash-exp)
- **Alibaba-NLP/gte-multilingual-base** – embeddings (768-dim, CPU, batch 32) — یکپارچه برای embedding و token counting
- **BAAI/bge-reranker-v2-m3** – reranker (ready, not yet active)
