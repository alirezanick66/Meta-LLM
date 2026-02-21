# 📋 README

## 🎨 اطلاعات کلی پروژه

| مشخصات             | جزئیات                                                         |
| ------------------ | -------------------------------------------------------------- |
| **نام پروژه**      | Meta                                                           |
| **هدف**            | سیستم پرسش و پاسخ هوشمند فارسی بر اساس مستندات شهرسازی و عمران |
| **کاربران همزمان** | حداکثر 5 نفر (با قابلیت scale در آینده)                        |
| **حجم داده**       | ~1000 صفحه (~3000-4000 chunks)                                 |
| **فرمت فایل‌ها**   | `.md` (Markdown)، `.docx` (Word)                               |
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

- **Embedding Model:** Alibaba-NLP/gte-multilingual-base (768-dim) ← _(تغییر از bge-m3)_
- **Device:** CPU با batch processing (batch_size: 32)
- **CPU Threads:** 4 (قابل تنظیم)
- **Tokenizer:** HooshvareLab/bert-fa-base-uncased (Persian) + gte-multilingual-base (Chunking)
- **Reranker:** BAAI/bge-reranker-v2-m3 (فاز 5 - آماده)
- **LLM Primary:** Groq API - llama-3.3-70b-versatile ✅
- **LLM Fallback:** Gemini API - gemini-2.0-flash-exp ✅
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
| `.docx` / `.doc`    | WordExtractor     | Heading→Markdown، table extraction، textbox support    |

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
BGE-Reranker-v2-m3 (آماده)
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
- **Vector Size:** 768 (gte-multilingual-base) ← _(تغییر از 1024)_
- **Distance:** COSINE
- **Point ID:** SHA-256(chunk_id)[:8] → int
- **Payload:** `{chunk_id, document_id, source, hierarchy, ...}`

### **BM25:**

- **Storage:** `backend/data/storage/bm25_cache/`
- **Files:**
    - `bm25_index.pkl` - BM25Okapi object
    - `chunk_mapping.pkl` - {chunk_ids, chunk_contents}

### **API Schemas:**

```python
class Source(BaseModel):
    index: int
    chunk_id: str
    source: str        # نام فایل
    hierarchy: str
    content: Optional[str]  # متن chunk (برای Source Cards)
```

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
- **WordExtractor: استخراج از .docx با Heading→Markdown، جداول، textbox** 🆕
- **DocumentProcessor: یکپارچه‌سازی multi-format با scan_folder** 🆕
- PersianNormalizer: نرمال‌سازی پیشرفته (بدون Hazm)
- MarkdownChunker: LangChain-based با header awareness
- File hashing (SHA-256) برای duplicate detection
- **Replace-by-filename logic: skip/replace بر اساس hash** 🆕

#### ✅ **فاز 4: Embedding & Indexing**

- EmbeddingService: **gte-multilingual-base** با CPU optimization ← _(تغییر از bge-m3)_
- QdrantIndexer: ذخیره vectors با Pydantic validation
- BM25Indexer: keyword indexing با rebuild قابلیت
- IndexingPipeline: orchestrator کامل با rollback
- **بهینه‌سازی Batch: skip_bm25_rebuild برای پردازش پوشه (BM25 یک‌بار در پایان)** 🆕

**مزایای تغییر مدل:**

- حجم: 305M (در مقابل 570M قبلی)
- سرعت: ~2x سریع‌تر روی CPU
- ابعاد vector: 768 (در مقابل 1024 قبلی)

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
- ✅ **PromptBuilder:** ساخت prompt بهینه با token counting + **ارسال content به sources** 🆕
- ✅ **GroqClient:** Groq API - llama-3.3-70b-versatile
- ✅ **GeminiClient:** Gemini API fallback - gemini-2.0-flash-exp
- ✅ **LLMOrchestrator:** مدیریت Primary/Fallback با metadata کامل

#### ✅ **فاز 9: API Layer**

- ✅ **FastAPI Application:** با lifespan management و CORS
- ✅ **Pydantic Schemas:** Request/Response validation
- ✅ **API Endpoints:**
    - `POST /api/chat` - RAG pipeline endpoint
    - `GET /api/stats` - آمار سیستم
    - `GET /health` - Health check با metrics
    - `GET /` - API documentation
    - **`DELETE /api/documents/{document_id}` - حذف یک سند** 🆕
    - **`POST /api/documents/bulk-delete` - حذف دسته‌ای با یک BM25 rebuild** 🆕
- ✅ **Exception Handling:** با traceback و type-based handling
- ✅ **Dependency Injection:** Singleton pattern برای services
- ✅ **Security:** path traversal protection با `Path(filename).name`

#### ✅ **فاز 10: Frontend**

- ✅ **React 18 + Vite:** Modern build tool
- ✅ **React Router DOM:** مسیریابی `/` و `/admin`
- ✅ **Tailwind CSS:** Utility-first styling با theme سفارشی
- ✅ **Components:**
    - `ChatInterface` - Main chat container
    - `Message` - با Markdown support و typing effect
    - `InputBox` - با character counter و send button
    - `MessageActions` - دکمه‌های Copy، Edit، Regenerate
    - `SkeletonMessage` - Loading state
    - `ScrollToBottom` - Floating scroll button
    - **`SourceCards` - نمایش منابع collapsible بعد از پایان typing** 🆕
    - **`SourceModal` - modal متن کامل chunk با نام فایل درست** 🆕
- ✅ **Admin Panel:** 🆕
    - `AdminPage` - صفحه مدیریت
    - `AdminLogin` - احراز هویت با password
    - `StatsCard` - نمایش آمار سیستم
    - `DocumentList` - لیست اسناد با multi-select delete
    - `UploadZone` - drag & drop upload با progress
    - دسترسی: URL مستقیم `/admin` یا 5 کلیک روی لوگو

**Styling:**

- Light theme (سفید/خاکستری)
- پیام کاربر: `#fff6d9` (زرد روشن)
- پیام ربات: بدون background
- دکمه ارسال: `#ffc414` (زرد طلایی)

**Structure:**

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx
│   │   ├── Message.jsx
│   │   ├── MessageActions.jsx
│   │   ├── InputBox.jsx
│   │   ├── SkeletonMessage.jsx
│   │   ├── ScrollToBottom.jsx
│   │   ├── SourceCards.jsx       # 🆕
│   │   ├── SourceModal.jsx       # 🆕
│   │   └── admin/                # 🆕
│   │       ├── AdminLogin.jsx
│   │       ├── StatsCard.jsx
│   │       ├── DocumentList.jsx
│   │       └── UploadZone.jsx
│   ├── hooks/
│   │   └── useTypingEffect.js
│   ├── pages/                    # 🆕
│   │   ├── ChatPage.jsx
│   │   └── AdminPage.jsx
│   ├── services/
│   │   ├── api.js
│   │   └── adminApi.js           # 🆕
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
		"react-router-dom": "^6.x",
		"axios": "^1.7.9",
		"react-markdown": "^9.0.0",
		"remark-gfm": "^4.0.0"
	}
}
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
- ⬜ Settings panel
- ⬜ Dark/Light mode toggle
- ⬜ Voice input
- ⬜ PDF support (text-based)
- ⬜ Streaming responses

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
│   │   │       ├── document_processor.py
│   │   │       ├── indexing_pipeline.py
│   │   │       ├── chunker.py
│   │   │       ├── markdown_extractor.py
│   │   │       └── word_extractor.py
│   │   └── utils/
│   ├── data/
│   └── main.py
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

### **6. مشکل dimension مغایرت Qdrant بعد از تغییر مدل embedding:** 🆕

```bash
# حذف collection قدیمی و ساخت مجدد
# (از طریق Qdrant dashboard یا API)
curl -X DELETE http://localhost:6333/collections/meta_documents
# سپس re-index همه اسناد
```

---

## 📄 License

این پروژه تحت لایسنس MIT منتشر شده است.

---

## 📌 اطلاعات نسخه

- **نسخه:** 1.1.0
- **آخرین بروزرسانی:** 2026-02-21
- **وضعیت:** فاز 10 تکمیل شد (با بهبودهای Phase 1) ✅
- **مرحله بعدی:** فاز 7 - Caching & Optimization یا فاز 11 - Advanced Features

---

**ساخته شده با ❤️ برای پاسخگویی هوشمند به سوالات شهرسازی و عمران**
