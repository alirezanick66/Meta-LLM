## 🎨 اطلاعات کلی پروژه

| **مشخصات** | **جزئیات** |
|------------|------------|
| **نام پروژه** | Meta |
| **هدف** | سیستم پرسش و پاسخ هوشمند فارسی بر اساس مستندات شهرسازی و عمران |
| **کاربران همزمان** | حداکثر 5 نفر (با قابلیت scale در آینده) |
| **حجم داده** | ~1000 صفحه Markdown (~3000-4000 chunks) |
| **فرمت فایل‌ها** | `.md` (Markdown) |
| **ساختار مستندات** | متنی با header hierarchy |
| **محیط استقرار** | VPS |
| **دسترسی کاربران** | همه کاربران به یک دیتابیس مشترک |
| **مدیریت فایل‌ها** | فایل‌ها داخل پروژه (`backend/data/documents/`) |

---

## 🏗️ معماری فنی

### **Backend:**
- **Framework**: FastAPI
- **Validation**: Pydantic (schema validation & type checking)
- **Database**: PostgreSQL (metadata & chunks)
- **Vector Store**: Qdrant (embeddings با SHA-256 point IDs)
- **Keyword Index**: BM25 (rank_bm25 با pickle storage)
- **Cache**: Redis (آماده برای فاز 7)

### **AI/ML Components:**
- **Embedding Model**: BAAI/bge-m3 (1024-dim)
- **Device**: CPU با batch processing (batch_size: 32)
- **CPU Threads**: 4 (قابل تنظیم)
- **Reranker**: BAAI/bge-reranker-v2-m3 *(فاز 5)*
- **LLM Primary**: Groq API *(فاز 6)*
- **LLM Fallback**: Gemini API *(فاز 6)*
- **Persian Processing**: Custom Normalizer (بدون Hazm، با `str.translate` برای سرعت)

### **Frontend:** *(فاز 10)*
- **Framework**: React
- **Styling**: Tailwind CSS
- **UI**: Chat Interface مدرن

### **DevOps:**
- **Containerization**: Docker & Docker Compose
- **Services**: PostgreSQL, Qdrant, Redis
- **Logging**: Loguru (فارسی‌سازی شده با `bidi` و `arabic_reshaper`)

---

## 📊 Data Processing Pipeline

### **1. Document Metadata:**
```python
{
    "source": "filename.md",
    "chunk_id": "doc_1_chunk_005",
    "document_id": 1,
    "chunk_index": 5,
    "title": "عنوان اصلی",
    "section": "بخش فرعی",
    "subsection": "زیربخش",
    "hierarchy": "عنوان > بخش > زیربخش",
    "has_list": True,
    "heading_level": 3,
    "token_count": 487,
    "created_at": "2026-02-13T10:26:00Z"
}
```

### **2. Chunking Strategy:**
- **Type**: Recursive with Header Awareness (LangChain)
- **Chunk Size**: 512 tokens (BGE-M3 tokenizer)
- **Overlap**: 128 tokens (25%)
- **Splitters**: 
  1. Markdown headers (`#`, `##`, `###`, `####`)
  2. Paragraphs (`\n\n`)
  3. Sentences (`,`, `.`)

**مزایا:**
- حفظ context با header injection
- سازگاری کامل با BGE-M3
- شناسایی لیست‌ها و ساختار
- تعداد چانک واقعی: **68 chunks** برای فایل نمونه (34,772 کاراکتر)

---

## 🔍 Retrieval Architecture *(فاز 5 - در حال توسعه)*

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
LLM (Groq → Gemini fallback)
    ↓
Final Answer
```

**Parameters:**
- BM25 retrieval: Top-20
- Vector retrieval: Top-20
- After reranking: Top-5
- Documents sent to LLM: 5

**چرا Hybrid؟**
- **BM25**: کلمات کلیدی دقیق فارسی (مثل "آیین‌نامه 2800")
- **Vector Search**: مفاهیم معنایی مشابه
- **Reranker**: افزایش دقت با cross-encoder

---

## 🗄️ Database Schema

### **PostgreSQL:**

#### **Table 1: `documents`**
```sql
id              INTEGER PRIMARY KEY
file_name       VARCHAR UNIQUE NOT NULL
file_path       TEXT NOT NULL
total_chunks    INTEGER DEFAULT 0
file_hash       VARCHAR(64) UNIQUE NOT NULL  -- SHA-256
indexed_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

#### **Table 2: `chunks`**
```sql
id              INTEGER PRIMARY KEY
document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE
chunk_id        VARCHAR(100) UNIQUE NOT NULL
content         TEXT NOT NULL
chunk_index     INTEGER NOT NULL
token_count     INTEGER NOT NULL
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()

INDEX idx_chunks_document_id
INDEX idx_chunks_chunk_index
```

### **Qdrant:**
```python
Collection: meta_documents
Vector Size: 1024 (BGE-M3)
Distance: COSINE
Point ID: SHA-256(chunk_id)[:8] → int
Payload: {chunk_id, document_id, source, hierarchy, ...}
```

### **BM25:**
```
Storage: backend/data/storage/bm25/
Files:
  - bm25_index.pkl        # BM25Okapi object
  - chunk_mapping.pkl     # {chunk_ids, chunk_contents}
```

---

## 🚀 Scalability Plan

| جزء | الان (5 کاربر) | آینده (50+ کاربر) |
|-----|----------------|-------------------|
| **FastAPI** | Single instance | Horizontal scaling (K8s) |
| **PostgreSQL** | Single instance | Connection pooling + replication |
| **Qdrant** | Single instance | Distributed cluster |
| **Redis** | Single instance | Cluster mode |
| **BM25** | In-memory | Distributed caching |

**معماری ماژولار = Scale آسان** ✅

---

## 📋 فازبندی پروژه

### 🟢 فازهای تکمیل شده:

#### ✅ **فاز 1: Setup و Infrastructure**
- ساختار پروژه ماژولار
- Docker Compose (PostgreSQL, Qdrant, Redis)
- Environment variables با Pydantic Settings
- `.gitignore` و فولدر structure

#### ✅ **فاز 2: Database Layer**
- PostgreSQL models (`Document`, `Chunk`)
- Alembic migrations
- Qdrant client با SHA-256 point IDs
- PostgresManager (CRUD operations)

#### ✅ **فاز 3: Document Processing**
- `MarkdownExtractor`: استخراج و تمیزسازی
- `PersianNormalizer`: نرمال‌سازی پیشرفته (بدون Hazm)
- `MarkdownChunker`: LangChain-based با header awareness
- File hashing (SHA-256) برای duplicate detection

#### ✅ **فاز 4: Embedding & Indexing**
- `EmbeddingService`: BGE-M3 با CPU optimization
- `QdrantIndexer`: ذخیره vectors با Pydantic validation
- `BM25Indexer`: keyword indexing با rebuild قابلیت
- `IndexingPipeline`: orchestrator کامل با rollback

**آمار تست موفق:**
```
✅ Document: enghelab.md
✅ Chunks: 68
✅ Tokens: 10,498
✅ Qdrant Vectors: 68
✅ BM25 Index: 68 chunks
⏱️ زمان اجرا: ~3 دقیقه
```

---

### 🔵 **فاز 5: Retrieval System** *(در حال توسعه)*
- [ ] BM25 Retriever
- [ ] Vector Retriever (Qdrant)
- [ ] Reciprocal Rank Fusion (RRF)
- [ ] BGE Reranker integration

### 🟣 **فاز 6: LLM Integration**
- [ ] Groq API client
- [ ] Gemini API fallback
- [ ] Prompt engineering
- [ ] Response streaming

### 🟤 **فاز 7: Caching & Optimization**
- [ ] Redis caching strategy
- [ ] Query cache
- [ ] Embedding cache

### ⚫ **فاز 8: Logging & Monitoring** ✅
- ✅ Loguru configuration
- ✅ Structured logging (فارسی)
- ✅ Error tracking

### 🔴 **فاز 9: API Layer**
- [ ] Chat endpoint
- [ ] Request/Response schemas
- [ ] Error handling

### 🟠 **فاز 10: Frontend**
- [ ] React + Vite
- [ ] Tailwind UI
- [ ] Chat Interface

### 🟡 **فاز 11: Integration & Testing**
- [ ] End-to-end tests
- [ ] Performance benchmarks

### 🟢 **فاز 12: Deployment**
- [ ] Production config
- [ ] Deployment guide

---

## 🎯 Priority Roadmap

### **🔴 Priority 1** *(فازهای 5-7)*
- Retrieval System کامل
- LLM Integration
- Redis Caching

### **🟡 Priority 2** *(Nice to Have)*
- Rate Limiting
- Health/Metrics endpoints
- Streaming responses
- Export chat
- Feedback system

### **🟢 Priority 3** *(Future)*
- Testing suite
- Admin panel
- Multi-document upload
- Advanced analytics

---

## 🛠️ راه‌اندازی محیط توسعه

### **1. نصب Dependencies:**
```bash
pip install -r requirements.txt
```

### **2. راه‌اندازی Docker:**
```bash
docker-compose up -d
```

### **3. بررسی وضعیت سرویس‌ها:**
```bash
docker-compose ps
```

### **4. اجرای Migrations:**
```bash
alembic upgrade head
```

### **5. تست Indexing:**
```bash
python scripts/test_full_indexing.py
```

### **6. مشاهده Logs:**
```bash
# Logs همه سرویس‌ها
docker-compose logs -f

# فقط Qdrant
docker-compose logs -f qdrant

# فقط PostgreSQL
docker-compose logs -f postgres
```

---

## 📂 ساختار پروژه

```
Meta/
├── backend/
│   ├── alembic/              # Database migrations
│   │   └── versions/
│   ├── app/
│   │   ├── core/             # Config, Database
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── db/               # Models, Managers
│   │   │   ├── models.py
│   │   │   ├── postgres.py
│   │   │   └── qdrant_client.py
│   │   ├── services/         # Business logic
│   │   │   ├── embedding_service.py
│   │   │   ├── markdown_extractor.py
│   │   │   ├── chunker.py
│   │   │   ├── qdrant_indexer.py
│   │   │   ├── bm25_indexer.py
│   │   │   └── indexing_pipeline.py
│   │   ├── schemas/          # Pydantic models
│   │   │   └── chunk_schemas.py
│   │   └── utils/            # Helpers
│   │       ├── logging_config.py
│   │       ├── custom_normalizer.py
│   │       └── hash_utils.py
│   ├── data/
│   │   ├── documents/        # فایل‌های .md
│   │   ├── storage/
│   │   │   └── bm25/         # BM25 cache
│   │   └── logs/             # Log files
│   └── main.py
├── scripts/                  # Test scripts
│   ├── test_normalizer.py
│   ├── test_markdown_extractor.py
│   ├── test_chunker.py
│   └── test_full_indexing.py
├── models/                   # مدل‌های دانلود شده
│   └── bge-m3/
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔧 تنظیمات محیطی (`.env`)

```bash
# API Keys
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=meta_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=meta_documents

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600

# Embedding Models
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_MODEL_PATH=models/bge-m3
EMBEDDING_MODEL_TOKEN=
EMBEDDING_VECTOR_DIM=1024
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
CPU_THREADS=4

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=128

# Retrieval
BM25_TOP_K=20
VECTOR_TOP_K=20
RERANKER_TOP_K=5

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
```

---

## 🧪 تست‌های موجود

### **1. تست Normalizer:**
```bash
python scripts/test_normalizer.py
```

### **2. تست Markdown Extractor:**
```bash
python scripts/test_markdown_extractor.py
```

### **3. تست Chunker:**
```bash
python scripts/test_chunker.py
```

### **4. تست کامل Indexing Pipeline:**
```bash
python scripts/test_full_indexing.py
```

**خروجی مورد انتظار:**
```
✅ تست موفقیت‌آمیز بود!
📄 Document ID: 3
🧩 Total Chunks: 68
📊 Qdrant Vectors: 68
📊 BM25 Chunks: 68
```

---


## 🐛 رفع مشکلات رایج

### **1. Qdrant Connection Error:**
```bash
# چک کردن وضعیت
docker-compose ps

# راه‌اندازی مجدد
docker-compose restart qdrant

# تست اتصال
curl http://localhost:6333/health
```

### **2. PostgreSQL Connection Error:**
```bash
# چک کردن logs
docker-compose logs postgres

# راه‌اندازی مجدد
docker-compose restart postgres
```

### **3. Memory Error در Embedding:**
```bash
# کاهش batch_size در .env
EMBEDDING_BATCH_SIZE=16
```

### **4. پاک کردن همه داده‌ها:**
```bash
# حذف volumes
docker-compose down -v

# راه‌اندازی مجدد
docker-compose up -d

# اجرای migrations
alembic upgrade head
```

---


## 📄 License

این پروژه تحت لایسنس MIT منتشر شده است.

---

**نسخه:** 1.0.0  
**آخرین بروزرسانی:** 2026-02-13  
**وضعیت:** فاز 4 تکمیل شد ✅  
**مرحله بعدی:** فاز 5 - Retrieval System

---

**ساخته شده با ❤️ برای پاسخگویی هوشمند به سوالات شهرسازی و عمران**