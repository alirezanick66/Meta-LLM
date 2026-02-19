# 📋 README

## 🎨 اطلاعات کلی پروژه

| مشخصات             | جزئیات                                                         |
| ------------------ | -------------------------------------------------------------- |
| **نام پروژه**      | Meta                                                           |
| **هدف**            | سیستم پرسش و پاسخ هوشمند فارسی بر اساس مستندات شهرسازی و عمران |
| **کاربران همزمان** | حداکثر 5 نفر (با قابلیت scale در آینده)                        |
| **حجم داده**       | ~1000 صفحه Markdown (~3000-4000 chunks)                        |
| **فرمت فایل‌ها**   | `.md` (Markdown)                                               |
| **ساختار مستندات** | متنی با header hierarchy                                       |
| **محیط استقرار**   | VPS                                                            |
| **دسترسی کاربران** | همه کاربران به یک دیتابیس مشترک                                |
| **مدیریت فایل‌ها** | فایل‌ها داخل پروژه (`backend/data/documents/`)                 |

---

## 🏗️ معماری فنی

### **Backend:**

- **Framework:** FastAPI
- **Validation:** Pydantic (schema validation & type checking)
- **Database:** PostgreSQL (metadata & chunks)
- **Vector Store:** Qdrant (embeddings با SHA-256 point IDs)
- **Keyword Index:** BM25 (rank_bm25 با pickle storage)
- **Cache:** Redis (آماده برای فاز 7)

### **AI/ML Components:**

- **Embedding Model:** BAAI/bge-m3 (1024-dim)
- **Device:** CPU با batch processing (batch_size: 32)
- **CPU Threads:** 4 (قابل تنظیم)
- **Tokenizer:** HooshvareLab/bert-fa-base-uncased (Persian) + BGE-M3 (Chunking)
- **Reranker:** BAAI/bge-reranker-v2-m3 (فاز 5 - آماده)
- **LLM Primary:** Groq API - llama-3.3-70b-versatile ✅
- **LLM Fallback:** Gemini API - gemini-2.0-flash-exp ✅
- **Persian Processing:** Custom Normalizer (بدون Hazm، با str.translate برای سرعت)

### **Frontend:**

- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State:** React Hooks
- **Markdown:** react-markdown + remark-gfm
- **UI Features:** Typing effect، Custom scrollbar، Skeleton loading، Markdown rendering

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
- **Chunk Size:** 512 tokens (BGE-M3 tokenizer)
- **Overlap:** 128 tokens (25%)
- **Splitters:**
    - Markdown headers (`#`, `##`, `###`, `####`)
    - Paragraphs (`\n\n`)
    - Sentences (`,`, `.`)

**مزایا:**

- حفظ context با header injection
- سازگاری کامل با BGE-M3
- شناسایی لیست‌ها و ساختار

**تعداد چانک واقعی:** 68 chunks برای فایل نمونه (34,772 کاراکتر)

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
BGE-Reranker-v2-m3 (آماده)
    ↓
Final Top-5 Documents
    ↓
┌──────────────────────────────┐
│   Prompt Builder             │
│  - Token counting (accurate) │
│  - System Q detection        │
│  - Source metadata           │
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

INDEX idx_chunks_document_id
INDEX idx_chunks_chunk_index
```

### **Qdrant:**

- **Collection:** meta_documents
- **Vector Size:** 1024 (BGE-M3)
- **Distance:** COSINE
- **Point ID:** SHA-256(chunk_id)[:8] → int
- **Payload:** `{chunk_id, document_id, source, hierarchy, ...}`

### **BM25:**

- **Storage:** `backend/data/storage/bm25/`
- **Files:**
    - `bm25_index.pkl` - BM25Okapi object
    - `chunk_mapping.pkl` - {chunk_ids, chunk_contents}

---

## 🚀 Scalability Plan

| جزء        | الان (5 کاربر)  | آینده (50+ کاربر)                |
| ---------- | --------------- | -------------------------------- |
| FastAPI    | Single instance | Horizontal scaling (K8s)         |
| PostgreSQL | Single instance | Connection pooling + replication |
| Qdrant     | Single instance | Distributed cluster              |
| Redis      | Single instance | Cluster mode                     |
| BM25       | In-memory       | Distributed caching              |

**معماری ماژولار = Scale آسان** ✅

---

## 📋 فازبندی پروژه

### 🟢 **فازهای تکمیل شده:**

#### ✅ **فاز 1: Setup و Infrastructure**

- ساختار پروژه ماژولار
- Docker Compose (PostgreSQL, Qdrant, Redis)
- Environment variables با Pydantic Settings
- .gitignore و فولدر structure

#### ✅ **فاز 2: Database Layer**

- PostgreSQL models (Document, Chunk)
- Alembic migrations
- Qdrant client با SHA-256 point IDs
- PostgresManager (CRUD operations با bulk methods)

#### ✅ **فاز 3: Document Processing**

- MarkdownExtractor: استخراج و تمیزسازی
- PersianNormalizer: نرمال‌سازی پیشرفته (بدون Hazm)
- MarkdownChunker: LangChain-based با header awareness
- File hashing (SHA-256) برای duplicate detection

#### ✅ **فاز 4: Embedding & Indexing**

- EmbeddingService: BGE-M3 با CPU optimization
- QdrantIndexer: ذخیره vectors با Pydantic validation
- BM25Indexer: keyword indexing با rebuild قابلیت
- IndexingPipeline: orchestrator کامل با rollback

**آمار تست موفق:**

- ✅ Document: enghelab.md
- ✅ Chunks: 68
- ✅ Tokens: 10,498
- ✅ Qdrant Vectors: 68
- ✅ BM25 Index: 68 chunks
- ⏱️ زمان اجرا: ~3 دقیقه

#### ✅ **فاز 5: Retrieval System**

- ✅ BM25 Retriever (keyword-based)
- ✅ Vector Retriever (Qdrant semantic search)
- ✅ Hybrid Retriever با Reciprocal Rank Fusion (RRF)
- ✅ Parallel execution (ThreadPoolExecutor)
- ✅ Score thresholds و filtering
- 🔵 BGE Reranker integration (آماده)

**Components:**

- `services/retrieval/bm25_indexer.py`
- `services/retrieval/vector_retriever.py`
- `services/retrieval/hybrid_retriever.py`

**Performance:**

- Sequential: ~400ms
- Parallel: ~220ms (45% faster)

#### ✅ **فاز 6: LLM Integration**

- ✅ **TokenizerService:** Singleton با lazy loading
- ✅ **PromptBuilder:** ساخت prompt بهینه با token counting
- ✅ **GroqClient:** Groq API - llama-3.3-70b-versatile
- ✅ **GeminiClient:** Gemini API fallback - gemini-2.0-flash-exp
- ✅ **LLMOrchestrator:** مدیریت Primary/Fallback با metadata کامل

**Features:**

- Lazy tokenizer loading
- System question detection
- Accurate token counting
- Source tracking
- Error recovery

#### ✅ **فاز 9: API Layer** 🆕

- ✅ **FastAPI Application:** با lifespan management و CORS
- ✅ **Pydantic Schemas:** Request/Response validation
    - Enums (LLMProvider, HealthStatus)
    - computed_field برای total_tokens
    - Pydantic V2 syntax
- ✅ **API Endpoints:**
    - `POST /api/chat` - RAG pipeline endpoint
    - `GET /api/stats` - آمار سیستم
    - `GET /health` - Health check با metrics
    - `GET /` - API documentation
- ✅ **Exception Handling:** با traceback و type-based handling
- ✅ **Dependency Injection:** Singleton pattern برای services
- ✅ **Performance Optimization:**
    - `run_in_threadpool` برای async-safe operations
    - Bulk database queries (N+1 حل شد)
    - Memory optimization با Singleton

**Components:**

- `app/api/routes.py` - API endpoints
- `app/api/dependencies.py` - Dependency injection
- `app/api/exceptions.py` - Exception handlers
- `app/schemas/api_schemas.py` - Pydantic models
- `app/main.py` - FastAPI application

**Performance Improvements:**

- Response Time: 14% faster (2650ms → 2270ms)
- DB Queries: 80% کمتر (N queries → 1 query)
- Concurrent Users: 10x بهتر (1 → 10+)

**Testing:**

- `scripts/test_api.py` - Automated API tests
- 6/6 tests passed ✅
- Coverage: Health, Stats, Chat (RAG + System Questions)

#### ✅ **فاز 10: Frontend** 🆕

- ✅ **React 18 + Vite:** Modern build tool
- ✅ **Tailwind CSS:** Utility-first styling با theme سفارشی
- ✅ **Components:**
    - `ChatInterface` - Main chat container (بدون header، minimal design)
    - `Message` - با Markdown support کامل و typing effect
    - `InputBox` - با character counter (0/1000) و gradient send button
    - `MessageActions` - دکمه‌های دایره‌ای با tooltip (Copy, Edit, Regenerate)
    - `SkeletonMessage` - Loading state
    - `ScrollToBottom` - Floating scroll button
- ✅ **Markdown Rendering:**
    - `react-markdown` + `remark-gfm` برای GitHub Flavored Markdown
    - پشتیبانی کامل: **Bold**, _Italic_, ~~Strikethrough~~
    - Code blocks با syntax highlighting و copy button
    - Lists (bullet & numbered)
    - Tables با border و hover effect
    - Links (clickable با target="\_blank")
    - Headings, Blockquotes, Horizontal Rules
- ✅ **Custom Hooks:**
    - `useTypingEffect` - Character-by-character typing
- ✅ **Features:**
    - ✅ RTL Support کامل (فارسی)
    - ✅ Responsive Design (موبایل + دسکتاپ)
    - ✅ Typing Effect با slideIn animation
    - ✅ Copy to clipboard با tooltip feedback
    - ✅ Edit mode برای پیام‌های کاربر (inline editing)
    - ✅ Regenerate با loading state
    - ✅ Scroll to bottom button (وقتی بالا رفتی)
    - ✅ Custom scrollbar (gradient، سمت راست)
    - ✅ Skeleton loading
    - ✅ Empty state با example questions و لوگوی متا
    - ✅ Error handling
    - ✅ Auto-scroll
    - ✅ Character counter (0/1000) با warning states
    - ✅ Keyboard shortcuts (Enter/Shift+Enter, Ctrl+Enter, ESC)

**Styling:**

- Light theme (سفید/خاکستری)
- پیام کاربر: `#fff6d9` (زرد روشن)
- پیام ربات: بدون background
- دکمه ارسال: `#ffc414` (زرد طلایی)
- دکمه‌های action: دایره‌ای با hover effect (gray-200)
- Tables: border-2 با hover effect روی rows
- Code blocks: background مشکی با copy button
- فونت: mikhak (local)

**UI Improvements:**

- ✅ حذف header (logo فقط در empty state)
- ✅ دکمه‌های دایره‌ای با tooltip (peer/target pattern)
- ✅ Edit mode با دکمه‌های Save/Cancel (مشکی/سفید)
- ✅ Markdown tables با border کامل از همه جهات
- ✅ Code blocks با language badge و copy button
- ✅ Inline code با background خاکستری و رنگ قرمز

**Structure:**

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx
│   │   ├── Message.jsx          # با Markdown support
│   │   ├── MessageActions.jsx   # با Edit button
│   │   ├── InputBox.jsx         # با counter و warning
│   │   ├── SkeletonMessage.jsx
│   │   └── ScrollToBottom.jsx
│   ├── hooks/
│   │   └── useTypingEffect.js
│   ├── services/
│   │   └── api.js
│   ├── index.css
│   └── main.jsx
├── index.html
├── tailwind.config.js
├── vite.config.js
└── package.json
```

**Dependencies:**

```json
{
	"dependencies": {
		"react": "^18.3.1",
		"react-dom": "^18.3.1",
		"axios": "^1.7.9",
		"react-markdown": "^9.0.0",
		"remark-gfm": "^4.0.0"
	}
}
```

**Development:**

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### 🔵 **فازهای بعدی:**

#### 🟤 **فاز 7: Caching & Optimization**

- ⬜ Redis caching strategy
- ⬜ Query cache
- ⬜ Embedding cache
- ⬜ Response cache
- ⬜ Connection pooling

#### ⚫ **فاز 8: Logging & Monitoring**

- ⬜ Advanced metrics
- ⬜ Performance monitoring
- ⬜ Error tracking dashboard

#### 🟡 **فاز 11: Advanced Features**

- ⬜ Sidebar + Chat history
- ⬜ Source cards با modal
- ⬜ Settings panel
- ⬜ Dark/Light mode toggle
- ⬜ Voice input

#### 🟢 **فاز 12: Deployment**

- ⬜ Production config
- ⬜ Docker production images
- ⬜ CI/CD pipeline
- ⬜ Deployment guide

---

## 🛠️ راه‌اندازی محیط توسعه

### **نصب و راه‌اندازی:**

#### **1. Backend:**

```bash
# نصب Dependencies
pip install -r requirements.txt

# راه‌اندازی Docker
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# اجرای Migrations
alembic upgrade head

# تست Indexing
python scripts/test_full_indexing.py

# اجرای API
uvicorn backend.app.main:app --reload
```

#### **2. Frontend:**

```bash
# نصب Dependencies
cd frontend
npm install

# اجرای Development Server
npm run dev

# Build برای Production
npm run build
```

### **تست‌ها:**

```bash
# تست API
python scripts/test_api.py

# تست Retrieval
python scripts/test_retrieval.py

# تست RAG Pipeline
python scripts/test_rag_pipeline.py
```

### **مشاهده Logs:**

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
│   ├── alembic/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   ├── dependencies.py
│   │   │   └── exceptions.py
│   │   ├── schemas/
│   │   │   └── api_schemas.py
│   │   ├── services/
│   │   │   ├── retrieval/
│   │   │   ├── llm/
│   │   │   └── document/
│   │   └── utils/
│   ├── data/
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── index.css
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── scripts/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🐛 رفع مشکلات رایج

### **1. Qdrant Connection Error:**

```bash
docker-compose restart qdrant
curl http://localhost:6333/health
```

### **2. PostgreSQL Connection Error:**

```bash
docker-compose logs postgres
docker-compose restart postgres
```

### **3. Frontend - CORS Error:**

```bash
# بررسی کنید Backend روشن است
curl http://localhost:8000/health

# بررسی Vite proxy config
cat frontend/vite.config.js
```

### **4. Frontend - VPN Issues:**

اگه با VPN مشکل دارید، در `vite.config.js`:

```js
server: {
  host: '127.0.0.1',  // بجای localhost
  port: 3000,
}
```

### **5. پاک کردن همه داده‌ها:**

```bash
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

---

## 📄 License

این پروژه تحت لایسنس MIT منتشر شده است.

---

## 📌 اطلاعات نسخه

- **نسخه:** 1.0.0
- **آخرین بروزرسانی:** 2026-02-19
- **وضعیت:** فاز 10 تکمیل شد ✅
- **مرحله بعدی:** فاز 7 - Caching & Optimization

---

**ساخته شده با ❤️ برای پاسخگویی هوشمند به سوالات شهرسازی و عمران**
