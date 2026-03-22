# 🛠️ DEVELOPMENT

---

## پیش‌نیازها

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

---

## 🚀 نصب و راه‌اندازی

### 1. Backend

```bash
# نصب dependencies
pip install -r backend/requirements.txt

# راه‌اندازی سرویس‌ها (PostgreSQL, Qdrant, Redis)
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# اجرای migrations
alembic upgrade head

# تست indexing
python scripts/test_full_indexing.py

# اجرای API
uvicorn backend.app.main:app --reload
```

### 2. Frontend

```bash
cd frontend

# نصب dependencies
npm install

# اجرای development server
npm run dev

# build برای production
npm run build
```

---

## 🧪 تست‌ها

```bash
# تست API
python scripts/test_api.py

# تست Retrieval
python scripts/test_retrieval.py

# تست RAG Pipeline
python scripts/test_rag_pipeline.py
```

---

## 📋 مشاهده Logs

```bash
# همه سرویس‌ها
docker-compose logs -f

# فقط Qdrant
docker-compose logs -f qdrant

# فقط PostgreSQL
docker-compose logs -f postgres
```

---

**نسخه:** 1.6.0 | **آخرین بروزرسانی:** 2026/03/21