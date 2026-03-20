## 🏗️ معماری فنی

### **Backend:**

- **Framework:** FastAPI
- **Validation:** Pydantic (schema validation & type checking)
- **Database:** PostgreSQL (metadata & chunks)
- **Vector Store:** Qdrant (embeddings با SHA-256 point IDs)
- **Keyword Index:** BM25 (rank_bm25 با pickle storage)
- **Cache:** Redis (آماده برای فاز 7)

### **AI/ML Components:**

- **Embedding Model:** Alibaba-NLP/gte-multilingual-base (768-dim)
- **Device:** CPU با batch processing (batch_size: 32)
- **CPU Threads:** 4 (قابل تنظیم)
- **Tokenizer:** gte-multilingual-base (یکپارچه برای chunking و token counting) 🆕
- **Reranker:** BAAI/bge-reranker-v2-m3 
- **LLM Primary:** Groq API - llama-3.3-70b-versatile ✅
- **LLM Fallback:** Gemini API - gemini-2.5-flash ✅
- **Persian Processing:** Custom Normalizer (بدون Hazm، با str.translate برای سرعت)

### **Frontend:**

- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Routing:** React Router DOM
- **State:** React Hooks
- **Markdown:** react-markdown + remark-gfm
- **UI Features:** Typing effect، Custom scrollbar، Skeleton loading، Markdown rendering، Source Cards، Admin Panel

### **DevOps:**

- **Containerization:** Docker & Docker Compose
- **Services:** PostgreSQL, Qdrant, Redis
- **Logging:** Loguru (فارسی‌سازی شده با bidi و arabic_reshaper)

## 📊 Data Processing Pipeline

### **1. Document Metadata:**

```json
{
	"source": "filename.md",
	"chunk_id": "doc_1_chunk_005",
	"document_id": 1,
	"chunk_index": 5,
	"title": "عنوان اصلی",
	"section": "بخش فرعی",
	"subsection": "زیربخش",
	"hierarchy": "عنوان > بخش > زیربخش",
	"has_list": true,
	"heading_level": 3,
	"token_count": 487,
	"created_at": "2026-02-13T10:26:00Z"
}
```

### **2. Chunking Strategy:**

- **Type:** Recursive with Header Awareness (LangChain)
- **Chunk Size:** 512 tokens (gte-multilingual-base tokenizer)
- **Overlap:** 128 tokens (25%)
- **Splitters:**
    - Markdown headers (`#`, `##`, `###`, `####`)
    - Paragraphs (`\n\n`)
    - Sentences (`,`, `.`)

**مزایا:**

- حفظ context با header injection
- سازگاری کامل با gte-multilingual-base
- شناسایی لیست‌ها و ساختار

### **3. فرمت‌های پشتیبانی‌شده:**

| فرمت                | Extractor         | ویژگی‌ها                                               |
| ------------------- | ----------------- | ------------------------------------------------------ |
| `.md` / `.markdown` | MarkdownExtractor | header hierarchy، list detection، front matter removal |
| `.docx`             | WordExtractor     | Heading→Markdown، table extraction، textbox support    |

**منطق Replace by Filename:**

- اگر فایل با همان نام قبلاً index شده و hash یکسان باشد → skip
- اگر hash تغییر کرده → حذف کامل و re-index
- اگر محتوا با فایل دیگری یکسان باشد → skip با warning

---

## 🔍 Retrieval Architecture

```
User Query
    ↓
Persian Normalization (Custom Normalizer)
    ↓
┌──────────────────────────────┐
│   Parallel Retrieval         │
├───────────────┬──────────────┤
│   BM25        │   Vector     │
│  (keyword)    │  (semantic)  │
│   Top-20      │   Top-20     │
└───────────────┴──────────────┘
    ↓
Reciprocal Rank Fusion (RRF)
    ↓
Merged Top-20 Results
    ↓
BGE-Reranker-v2-m3 
    ↓
Final Top-5 Documents
    ↓
┌──────────────────────────────┐
│   Prompt Builder             │
│  - Token counting (accurate) │
│  - System Q detection        │
│  - Source metadata + content │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│   LLM Orchestrator           │
│  Primary: Groq (llama-3.3)   │
│  Fallback: Gemini (flash)    │
└──────────────────────────────┘
    ↓
Final Answer + Sources
```

### **Parameters:**

- BM25 retrieval: Top-20
- Vector retrieval: Top-20
- After RRF: Top-20 merged
- Documents sent to LLM: 5
- Max context tokens: 3000

**چرا Hybrid؟**

- **BM25:** کلمات کلیدی دقیق فارسی (مثل "آیین‌نامه 2800")
- **Vector Search:** مفاهیم معنایی مشابه
- **RRF:** ترکیب هوشمند نتایج

---

## 🗄️ Database Schema

### **PostgreSQL:**

**Table 1: documents**

```sql
id              INTEGER PRIMARY KEY
file_name       VARCHAR UNIQUE NOT NULL
file_path       TEXT NOT NULL
total_chunks    INTEGER DEFAULT 0
file_hash       VARCHAR(64) UNIQUE NOT NULL  -- SHA-256
indexed_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

**Table 2: chunks**

```sql
id              INTEGER PRIMARY KEY
document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE
chunk_id        VARCHAR(100) UNIQUE NOT NULL
content         TEXT NOT NULL
chunk_index     INTEGER NOT NULL
token_count     INTEGER NOT NULL
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()

INDEX idx_chunks_document_id
INDEX idx_chunks_chunk_index
```

### **Qdrant:**

- **Collection:** meta_documents
- **Vector Size:** 768 (gte-multilingual-base)
- **Distance:** COSINE
- **Point ID:** SHA-256(chunk_id)[:8] → int
- **Payload:** `{chunk_id, document_id, source, hierarchy, ...}`

### **BM25:**

- **Storage:** `backend/data/storage/bm25_cache/`
- **Files:**
    - `bm25_index.pkl` - BM25Okapi object
    - `chunk_mapping.pkl` - {chunk_ids, chunk_contents}

---

## 🧱 LLM Layer Architecture

### **لایه‌بندی داخلی:**

```
LLMUsage           ← مصرف توکن (shared بین لایه‌ها) — @dataclass frozen
SourceInfo         ← اطلاعات منبع (shared بین لایه‌ها) — @dataclass frozen
PromptResult       ← خروجی PromptBuilder              [Layer 1]
ProviderLLMResponse← خروجی Groq/Gemini                [Layer 2]
LLMResponse        ← خروجی نهایی به routes.py         [Layer 3]
```

### **لایه‌بندی Usage:**

| کلاس        | نوع                 | لایه  | کاربرد                   |
| ----------- | ------------------- | ----- | ------------------------ |
| `LLMUsage`  | `@dataclass frozen` | داخلی | groq/gemini/orchestrator |
| `UsageInfo` | Pydantic BaseModel  | API   | routes.py → frontend     |

### **Dependency Injection — Singletons:**

همه سرویس‌های سنگین با `@lru_cache(maxsize=1)` در `dependencies.py` مدیریت می‌شوند:

```python
get_embedding_service()   # EmbeddingService
get_tokenizer_service()   # TokenizerService
get_qdrant_manager()      # QdrantManager
get_bm25_indexer()        # BM25Indexer
get_qdrant_indexer()      # QdrantIndexer
get_hybrid_retriever()    # HybridRetriever
get_llm_orchestrator()    # LLMOrchestrator
```

> **نکته:** `IndexingPipeline` عمداً per-request است چون به `db_session` per-request وابسته است.

---


**Schema های یکپارچه برای Retrieval (StrEnum):** 🆕

```python
# backend/app/schemas/retrieval_schemas.py
class RetrievalMethod(StrEnum)   # BM25, VECTOR
class ResultKeys(StrEnum)        # CHUNK_ID, SCORE, RETRIEVAL_METHOD, METADATA, CONTENT
class RRFKeys(StrEnum)           # RRF_SCORE, BM25_SCORE, VECTOR_SCORE, BM25_RANK, VECTOR_RANK
class RRFStats(StrEnum)          # BOTH, ONLY_BM25, ONLY_VECTOR
```

**Performance:**

- Sequential: ~400ms
- Parallel: ~220ms (45% faster)



**Schema های لایه‌بندی‌شده LLM:** 🆕

```python
# backend/app/schemas/llm_schemas.py  — ترتیب تعریف مهم است
@dataclass(frozen=True) LLMUsage          # Layer shared
@dataclass(frozen=True) SourceInfo        # Layer shared — قبل از PromptResult تعریف می‌شود
@dataclass(frozen=True) PromptResult      # Layer 1
@dataclass(frozen=True) ProviderLLMResponse  # Layer 2 — با create_error factory
@dataclass(frozen=True) LLMResponse       # Layer 3 — با from_provider_response
```


## 📂 ساختار پروژه

```
Meta/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   └── postgres.py
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   ├── dependencies.py       
│   │   │   └── exceptions.py
│   │   ├── schemas/
│   │   │   ├── base_schemas.py       
│   │   │   ├── api_schemas.py        
│   │   │   ├── chat_schemas.py       
│   │   │   ├── chunk_schemas.py      
│   │   │   ├── llm_schemas.py        
│   │   │   └── retrieval_schemas.py 
│   │   ├── services/
│   │   │   ├── embedding/
│   │   │   │   ├── embedding_service.py
│   │   │   │   └── tokenizer_service.py
│   │   │   ├── vector/
│   │   │   │   ├── qdrant_client.py
│   │   │   │   └── qdrant_indexer.py
│   │   │   ├── retrieval/
│   │   │   │   ├── bm25_indexer.py
│   │   │   │   ├── vector_retriever.py
│   │   │   │   └── hybrid_retriever.py
│   │   │   ├── document/
│   │   │   │   ├── document_processor.py
│   │   │   │   ├── indexing_pipeline.py
│   │   │   │   ├── chunker.py
│   │   │   │   ├── markdown_extractor.py
│   │   │   │   └── word_extractor.py
│   │   │   └── llm/
│   │   │       ├── groq_client.py
│   │   │       ├── gemini_client.py
│   │   │       ├── prompt_builder.py
│   │   │       └── llm_orchestrator.py
│   │   ├── utils/
│   │   │   ├── logging_config.py
│   │   │   ├── custom_normalizer.py
│   │   │   └── hash_utils.py
│   │   └── main.py
│   ├── data/
│   │   ├── documents/               
│   │   └── storage/
│   │       └── bm25_cache/           
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── admin/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   └── index.css
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── scripts/
├── docker-compose.yml
└── README.md
```
