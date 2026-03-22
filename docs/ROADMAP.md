# 🗺️ ROADMAP

---

## 🟢 فازهای تکمیل شده

#### ✅ فاز 1: Setup و Infrastructure

- ساختار پروژه ماژولار
- Docker Compose (PostgreSQL, Qdrant, Redis)
- Environment variables با Pydantic Settings
- .gitignore و فولدر structure

#### ✅ فاز 2: Database Layer

- PostgreSQL models (Document, Chunk)
- Alembic migrations
- Qdrant client با SHA-256 point IDs
- PostgresManager (CRUD operations با bulk methods)

#### ✅ فاز 3: Document Processing

- MarkdownExtractor: استخراج و تمیزسازی
- WordExtractor: استخراج از .docx با Heading→Markdown، جداول، textbox
- DocumentProcessor: یکپارچه‌سازی multi-format با scan_folder
- PersianNormalizer: نرمال‌سازی پیشرفته (بدون Hazm)
- MarkdownChunker: LangChain-based با header awareness و پشتیبانی از Header 4
- File hashing (SHA-256) برای duplicate detection
- Replace-by-filename logic: skip/replace بر اساس hash

#### ✅ فاز 4: Embedding & Indexing

- EmbeddingService: gte-multilingual-base با CPU optimization
    - استفاده از `get_sentence_embedding_dimension()` به جای test embedding
    - `convert_to_numpy=True` برای حذف type check های اضافه
    - Batch insert با `BATCH_SIZE=100` در Qdrant
- TokenizerService: یکپارچه‌سازی با gte-multilingual-base (حذف tokenizer فارسی جداگانه)
- QdrantIndexer: ذخیره vectors با Pydantic validation
- BM25Indexer: keyword indexing با rebuild قابلیت، thread-safe با `RLock`
- IndexingPipeline: orchestrator کامل با rollback
- بهینه‌سازی Batch: skip_bm25_rebuild برای پردازش پوشه (BM25 یک‌بار در پایان)

#### ✅ فاز 5: Retrieval System

- BM25 Retriever (keyword-based)
- Vector Retriever (Qdrant semantic search)
- Hybrid Retriever با Reciprocal Rank Fusion (RRF)
- Parallel execution (ThreadPoolExecutor) — حذف sequential fallback
- Score thresholds و filtering
- gte-multilingual-reranker-base
- - Content fetch از PostgreSQL بین RRF و Reranker (حل باگ reranker score=0.0001)
- تقسیم `retrieve` به دو متد `retrieve` و `rerank`
- `bge-reranker-base` به جای `v2-m3` (بهینه‌سازی CPU)

#### ✅ فاز 6: LLM Integration

- TokenizerService: Singleton با lazy loading و thread safety
- PromptBuilder: ساخت prompt بهینه با token budget دقیق + ارسال content به sources
    - تشخیص سوالات سیستمی با Regex (fullmatch)
    - محاسبه overhead بدون system_prompt (API جداگانه حساب می‌کند)
    - `system_tokens` cache شده در `__init__`
- GroqClient: Groq API — llama-3.3-70b-versatile با `FinishReason` Enum
- GeminiClient: Gemini API fallback — gemini-2.5-flash با `_parse_finish_reason` ایمن
- LLMOrchestrator: مدیریت Primary/Fallback با `LLMProvider` Enum
- - IntentDetector: سه‌لایه (Regex + LLM با CONVERSATIONAL + پیام ثابت بدون LLM call)
- `generate_answer` با `intent` از بیرون (حذف double detection)

#### ✅ فاز 9: API Layer

- FastAPI Application: با lifespan management و CORS
- Pydantic Schemas: Request/Response validation
- API Endpoints:
    - `POST /api/chat` — RAG pipeline endpoint
    - `GET /api/stats` — آمار سیستم
    - `GET /health` — Health check با metrics
    - `GET /` — API documentation
    - `DELETE /api/documents/{document_id}` — حذف یک سند
    - `POST /api/documents/bulk-delete` — حذف دسته‌ای با یک BM25 rebuild
- Exception Handling: با traceback و type-based handling
- Dependency Injection: Singleton pattern با `@lru_cache` برای همه سرویس‌ها
- Security: path traversal protection با `Path(filename).name`
- `_create_pipeline()` helper: حذف تکرار ساخت `IndexingPipeline` در routes

#### ✅ فاز 10: Frontend

- React 18 + Vite: Modern build tool
- React Router DOM: مسیریابی `/` و `/admin`
- Tailwind CSS: Utility-first styling با theme سفارشی
- Components:
    - `ChatInterface` — Main chat container
    - `Message` — با Markdown support و typing effect
    - `InputBox` — با character counter و send button
    - `MessageActions` — دکمه‌های Copy، Edit، Regenerate
    - `SkeletonMessage` — Loading state
    - `ScrollToBottom` — Floating scroll button
    - `SourceCards` — نمایش منابع collapsible بعد از پایان typing
    - `SourceModal` — modal متن کامل chunk با نام فایل درست
- Admin Panel:
    - `AdminPage` — صفحه مدیریت
    - `AdminLogin` — احراز هویت با password
    - `StatsCard` — نمایش آمار سیستم
    - `DocumentList` — لیست اسناد با multi-select delete
    - `UploadZone` — drag & drop upload با progress

---

## 🔵 فازهای بعدی

#### 🟤 فاز 7: Caching & Optimization

- ⬜ Redis caching strategy
- ⬜ Query cache
- ⬜ Embedding cache
- ⬜ Response cache
- ⬜ Connection pooling

#### ⚫ فاز 8: Logging & Monitoring

- ⬜ Advanced metrics
- ⬜ Performance monitoring
- ⬜ Error tracking dashboard

#### 🟡 فاز 11: Advanced Features

- ⬜ Sidebar + Chat history
- ⬜ Settings panel
- ⬜ Dark/Light mode toggle
- ⬜ Voice input
- ⬜ PDF support (text-based)
- ⬜ Streaming responses
- ⬜اضافه کردن Query Expansion به لیست
#### 🟢 فاز 12: Deployment

- ⬜ Production config
- ⬜ Docker production images
- ⬜ CI/CD pipeline
- ⬜ Deployment guide

---

**نسخه:** 1.5.0 | **آخرین بروزرسانی:** 2026/03/22