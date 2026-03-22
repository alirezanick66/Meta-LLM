# 🏗️ معماری فنی

---

## ⚙️ Stack فنی

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
- **Tokenizer:** gte-multilingual-base (یکپارچه برای chunking و token counting)
- **Reranker:** gte-multilingual-reranker-base
- **LLM Primary:** Groq API — llama-3.3-70b-versatile
- **LLM Fallback:** Gemini API — gemini-2.5-flash
- **Persian Processing:** Custom Normalizer (بدون Hazm، با str.translate برای سرعت)

### **Frontend:**

- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Routing:** React Router DOM
- **Markdown:** react-markdown + remark-gfm
- **UI Features:** Typing effect، Skeleton loading، Source Cards، Admin Panel

### **DevOps:**

- **Containerization:** Docker & Docker Compose
- **Services:** PostgreSQL, Qdrant, Redis
- **Logging:** Loguru (فارسی‌سازی شده با bidi و arabic_reshaper)

---

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
- **Splitters:** Markdown headers، Paragraphs (`\n\n`)، Sentences (`,`, `.`)

### **3. فرمت‌های پشتیبانی‌شده:**

|فرمت|Extractor|ویژگی‌ها|
|---|---|---|
|`.md` / `.markdown`|MarkdownExtractor|header hierarchy، list detection، front matter removal|
|`.docx`|WordExtractor|Heading→Markdown، table extraction، textbox support|

### **4. منطق Replace by Filename:**

- hash یکسان با فایل قبلی → skip
- hash تغییر کرده → حذف کامل و re-index
- محتوا با فایل دیگری یکسان → skip با warning

---

## 🔍 Retrieval Architecture

```
User Query
    ↓
Intent Detection (Regex → LLM Classifier)
    ├── CONVERSATIONAL → پیام ثابت (بدون API call)
    ├── OUT_OF_SCOPE   → پیام ثابت (بدون API call)
    └── RAG ↓
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
Content Fetch from PostgreSQL (Bulk Query)
    ↓
gte-multilingual-reranker-base (Top-8 input → Top-5 output)
    ↓
Final Top-5 Documents
    ↓
┌──────────────────────────────┐
│   Prompt Builder             │
│  - Token counting (accurate) │
│  - Intent-based routing      │
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

|         پارامتر          | مقدار         |
| :----------------------: | ------------- |
|      BM25 retrieval      | Top-20        |
|     Vector retrieval     | Top-20        |
|        After RRF         | Top-20 merged |
|  Documents sent to LLM   | Top-5         |
|    Max context tokens    | 3000          |
|   RERANKER_INPUT_SIZE    | 8             |
| RERANKER_SCORE_THRESHOLD | 0.1           |

### **چرا Hybrid؟**

- **BM25:** کلمات کلیدی دقیق فارسی (مثل "آیین‌نامه 2800")
- **Vector Search:** مفاهیم معنایی مشابه
- **RRF:** ترکیب هوشمند بدون نیاز به تنظیم وزن دستی

---

## 🗄️ Database Schema

### **PostgreSQL:**

**Table: documents**

```sql
id              INTEGER PRIMARY KEY
file_name       VARCHAR UNIQUE NOT NULL
file_path       TEXT NOT NULL
total_chunks    INTEGER DEFAULT 0
file_hash       VARCHAR(64) UNIQUE NOT NULL  -- SHA-256
indexed_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

**Table: chunks**

```sql
id              INTEGER PRIMARY KEY
document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE
chunk_id        VARCHAR(100) UNIQUE NOT NULL
content         TEXT NOT NULL
chunk_index     INTEGER NOT NULL
token_count     INTEGER NOT NULL
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

### **Qdrant:**

- **Collection:** meta_documents
- **Vector Size:** 768 (gte-multilingual-base)
- **Distance:** COSINE
- **Point ID:** SHA-256(chunk_id)[:8] → int
- **Payload:** `{chunk_id, document_id, source, hierarchy, ...}`

### **BM25:**

- **Storage:** `backend/data/storage/bm25_cache/`
- **Files:** `bm25_index.pkl` (BM25Okapi object)، `chunk_mapping.pkl` (chunk_ids + contents)

---

## 🧱 LLM Layer

### **لایه‌بندی داخلی:**

```
LLMUsage            ← مصرف توکن (shared)
SourceInfo          ← اطلاعات منبع (shared)
PromptResult        ← خروجی PromptBuilder       [Layer 1]
ProviderLLMResponse ← خروجی Groq/Gemini         [Layer 2]
LLMResponse         ← خروجی نهایی به API        [Layer 3]
```

### **استراتژی Fallback:**

- Primary: Groq — در صورت خطا یا timeout
- Fallback: Gemini — به صورت خودکار
- هر دو پاسخ از طریق `LLMResponse` یکسان به API برمی‌گردند

---

## 📂 ساختار پروژه

```
MetaLLM/
├── .github/                        ← GitHub configuration
├── docs/                           ← مستندات فنی و منابع
│   ├── .obsidian/                  ← تنظیمات Obsidian
│   ├── corpus/                     ← فایل‌های قانونی (منابع RAG)
│   │   ├── ghanoone_kar.md
│   │   ├── tamin.md
│   │   ├── bikari.md
│   │   ├── mozd_1404.md
│   │   └── ghanoone_madani.md
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── ROADMAP.md
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── embedding/
│   │   │   ├── vector/
│   │   │   ├── retrieval/
│   │   │   ├── document/
│   │   │   └── llm/
│   │   ├── utils/
│   │   └── main.py
│   ├── data/
│        ├── storage/
│        │   └── bm25_cache/
│        └── logs/
│  
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   │   └── fonts/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── scripts/
├── .gitignore
├── alembic.ini
├── requirements.txt
└── docker-compose.yml
```

**نسخه:** 1.5.0 | **آخرین بروزرسانی:** 2026/03/22