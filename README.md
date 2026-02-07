**📋 README**

**🎨 اطلاعات کلی پروژه**

|**مشخصات**|**جزئیات**|
| -: | -: |
|**نام پروژه**|Meta|
|**هدف**|سیستم پرسش و پاسخ هوشمند فارسی بر اساس مستندات شهرسازی و عمران|
|**کاربران همزمان**|حداکثر 5 نفر (با قابلیت scale در آینده)|
|**حجم داده**|~1000 صفحه Word |
|**فرمت فایل‌ها**|فقط .docx|
|**ساختار مستندات**|متنی (بدون ساختار پیچیده)|
|**محیط استقرار**|VPS|
|**دسترسی کاربران**|همه کاربران به یک دیتابیس مشترک|
|**مدیریت فایل‌ها**|فایل‌ها داخل پروژه قرار می‌گیرند (بدون نیاز به Admin Panel)|

-----
**🏗️ معماری فنی**

**Backend:**

- **Framework**: FastAPI
- **Validation**: Pydantic (برای schema validation و type checking)
- **Database**: PostgreSQL
- **Vector Store**: Qdrant (روی Docker)
- **Cache**: Redis (روی Docker)

**AI/ML Components:**

- **Embedding Model**: BAAI/bge-m3
- **Device**: CPU (با batch processing برای بهینه‌سازی)
- **Reranker**: BAAI/bge-reranker-v2-m3
- **LLM Primary**: Groq API
- **LLM Fallback**: Gemini API
- **Persian Processing**: Hazm (نسخه استاندارد، در صورت نیاز به custom تغییر می‌کنه)

**Frontend:**

- **Framework**: React
- **Styling**: Tailwind CSS
- **UI**: مدرن و زیبا با Chat Interface

**DevOps:**

- **Containerization**: Docker & Docker Compose
- **Logging**: Loguru (بدون rotation)
-----
**📊 Data Processing Pipeline**

**1. Document Metadata:**

\- source: نام فایل (filename.docx)

\- chunk\_id: شناسه یکتا (doc1\_chunk\_5)

\- page\_range: محدوده صفحات تقریبی

\- total\_chunks: تعداد کل چانک‌های سند

\- created\_at: زمان ایندکس

**2. Chunking Strategy:**

Type: Fixed-Size with Overlap

Chunk Size: 512 tokens

Overlap: 128 tokens (25%)

**دلایل انتخاب:**

- حفظ context بین چانک‌ها
- سازگار با BGE-M3
- performance بهتر
- retrieval دقیق‌تر
- تعداد چانک تقریبی: 3000-4000 (برای 1000 صفحه)
-----
**🔍 Retrieval Architecture**

**Hybrid Retrieval System:**

User Query

`    `↓

Persian Normalization (Hazm)

`    `↓

┌────────────────────────────┐

│   Parallel Retrieval       │

├─────────────┬──────────────┤

│   BM25      │   Vector     │

│  (keyword)  │  (semantic)  │

│   Top-20    │   Top-20     │

└─────────────┴──────────────┘

`    `↓

Reciprocal Rank Fusion (RRF)

`    `↓

Merged Top-20 Results

`    `↓

BGE-Reranker-v2-m3

`    `↓

Final Top-5 Documents

`    `↓

LLM (Groq → Gemini fallback)

`    `↓

Final Answer

**Parameters:**

- BM25 retrieval: Top-20
- Vector retrieval: Top-20
- After reranking: Top-5
- Documents sent to LLM: 5

**چرا Hybrid؟**

- BM25: پیدا کردن کلمات کلیدی دقیق فارسی (مثل "آیین‌نامه 2800")
- Vector Search: پیدا کردن مفاهیم معنایی مشابه
- Reranker: افزایش دقت با cross-encoder
-----
**🗄️ Database Schema (PostgreSQL)**

**Table 1: documents**

\- id (Primary Key)

\- filename (Unique)

\- file\_path

\- total\_pages

\- total\_chunks

\- indexed\_at (Timestamp)

\- file\_hash (Unique) → برای تشخیص تغییرات

**Table 2: chunks**

\- id (Primary Key)

\- document\_id (Foreign Key → documents)

\- chunk\_id (Unique)

\- content (Text)

\- chunk\_index (موقعیت در سند)

\- token\_count

\- page\_range

\- created\_at (Timestamp)

**Indexes:**

- idx\_chunks\_document
- idx\_chunks\_chunk\_id

**نقش SQL:**

- مدیریت metadata
- ردیابی اسناد ایندکس شده
- Qdrant فقط embeddings و vector\_id ذخیره می‌کنه
-----
**🚀 Scalability Plan**

**الان (5 کاربر):**

- FastAPI با 4 workers
- Redis single instance
- Qdrant single instance
- PostgreSQL single instance

**آینده (50+ کاربر):**

- FastAPI: Horizontal scaling (Docker Swarm/Kubernetes)
- Redis: Cluster mode با replication
- Qdrant: Distributed cluster
- PostgreSQL: با connection pooling

**خبر خوب:** معماری ماژولار طراحی می‌شه، پس scale راحته!

-----
**📋 لیست کارها (Priority-based)**

**🔴 Priority 1 - Core Features (شروع فوری):**

1. ✅ Backend structure setup
1. ✅ Document processing pipeline (docx → chunks)
1. ✅ Hazm normalization
1. ✅ Embeddings با BGE-M3 (CPU + batch)
1. ✅ PostgreSQL schema + models
1. ✅ Qdrant integration
1. ✅ BM25 indexing
1. ✅ Hybrid retrieval (BM25 + Vector + RRF)
1. ✅ Reranker integration
1. ✅ LLM service (Groq + Gemini fallback)
1. ✅ Redis caching
1. ✅ Loguru logging
1. ✅ FastAPI endpoints
1. ✅ Docker Compose setup
1. ✅ Frontend (React + Tailwind) - Chat Interface

**🟡 Priority 2 - Nice to Have (بعداً):**

- Rate Limiting برای Groq
- Custom Normalizer 
- Health/Metrics endpoints
- Streaming responses
- Dark mode
- Export chat به PDF/Word
- Suggested questions
- Feedback system (Like/Dislike)

**🟢 Priority 3 - Future (آینده):**

- Testing suite
- Admin panel برای مدیریت اسناد
- Multi-language support
- Advanced analytics