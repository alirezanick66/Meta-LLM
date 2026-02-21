# 🚀 راهنمای سریع راه‌اندازی Meta API

## 📋 پیش‌نیازها

```bash
# بررسی Python
python --version  # باید 3.9+ باشد

# بررسی Docker
docker --version
docker-compose --version
```

---

## ⚡ راه‌اندازی سریع (5 دقیقه)

### مرحله 1: راه‌اندازی Docker Services

```bash
cd /path/to/Meta
docker-compose up -d
```

**چک کردن:**

```bash
docker-compose ps
# همه سرویس‌ها باید UP باشند
```

---

### مرحله 2: اجرای Migrations

```bash
alembic upgrade head
```

**خروجی موفق:**

```
INFO  [alembic.runtime.migration] Running upgrade -> 3d9c51c8711f
INFO  [alembic.runtime.migration] Running upgrade 3d9c51c8711f -> ea2f429d9c35
```

---

### مرحله 3: Indexing اولیه (اگه هنوز نکردی)

```bash
python scripts/test_full_indexing.py
```

**خروجی موفق:**

```
✅ تست موفقیت‌آمیز بود!
📄 Document ID: 1
🧩 Total Chunks: 68
```

---

### مرحله 4: اجرای API Server

```bash
# روش 1: با uvicorn مستقیم (توصیه شده برای dev)
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# روش 2: با python
python backend/app/main.py

# روش 3: با script مستقیم
python -m uvicorn backend.app.main:app --reload
```

**خروجی موفق:**

```
🚀 Meta API در حال راه‌اندازی...
✅ PostgreSQL متصل است
✅ Qdrant متصل است - Vectors: 68
✅ Meta API آماده است!
📚 Docs: http://localhost:8000/docs
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 تست API

### 1. تست ساده با مرورگر

باز کن: http://localhost:8000

**پاسخ باید باشه:**

```json
{
  "message": "به Meta API خوش آمدید",
  "status": "running",
  ...
}
```

---

### 2. Health Check

```bash
curl http://localhost:8000/health
```

**خروجی:**

```json
{
	"status": "healthy",
	"components": {
		"postgres": "connected",
		"qdrant": "connected"
	}
}
```

---

### 3. تست Chat (اصلی)

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟",
    "temperature": 0.3
  }'
```

**خروجی موفق:**

```json
{
  "success": true,
  "answer": "انقلاب اسلامی تأثیرات عمیقی...",
  "sources": [...],
  "metadata": {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    ...
  }
}
```

---

### 4. تست خودکار (همه endpoints)

```bash
python scripts/test_api.py
```

---

## 🎨 Swagger UI (Interactive Testing)

باز کن: http://localhost:8000/docs

**مراحل:**

1. روی `/api/chat` کلیک کن
2. "Try it out" بزن
3. Request body رو پر کن
4. "Execute" بزن
5. نتیجه رو ببین

---

## 🐛 حل مشکلات رایج

### مشکل 1: سرویس‌ها بالا نیومدن

```bash
# چک logs
docker-compose logs postgres
docker-compose logs qdrant

# راه‌اندازی مجدد
docker-compose down -v
docker-compose up -d
```

---

### مشکل 2: API اجرا نمیشه

```bash
# چک Port در حال استفاده نباشه
lsof -i :8000

# یا Port دیگه‌ای استفاده کن
uvicorn backend.app.main:app --port 8001
```

---

### مشکل 3: خطای Import

```bash
# مطمئن شو که در ریشه پروژه هستی
pwd  # باید Meta/ باشه

# یا PYTHONPATH رو ست کن
export PYTHONPATH="${PYTHONPATH}:/path/to/Meta"
```

---

### مشکل 4: API جواب نمیده (Timeout)

```bash
# چک Health
curl http://localhost:8000/health

# چک Logs
tail -f backend/data/logs/api.log
```

---

## 📊 Monitoring در Production

### چک کردن وضعیت

```bash
# Health check (هر 30 ثانیه)
watch -n 30 'curl -s http://localhost:8000/health | jq'

# Stats
curl http://localhost:8000/api/stats | jq
```

### لاگ‌ها

```bash
# API logs
tail -f backend/data/logs/api.log

# تمام لاگ‌ها
tail -f backend/data/logs/*.log
```

---

## 🔧 تنظیمات مهم (.env)

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True  # فقط dev، در production False

# LLM Settings
TEMPERATURE=0.3
MAX_TOKENS=2048
LLM_TIMEOUT=30

# Retrieval Settings
BM25_TOP_K=20
VECTOR_TOP_K=20
RERANKER_TOP_K=5
```

---

## 🎯 Example Queries

### سوالات تستی خوب:

```
1. "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟"
2. "نقش امام خمینی در انقلاب چه بود؟"
3. "ویژگی‌های انقلاب اسلامی ایران چیست؟"
4. "تو کی هستی؟" (سوال سیستمی)
```

---

## 📞 نیاز به کمک؟

1. **چک کن:** لاگ‌ها در `backend/data/logs/`
2. **تست کن:** `/health` endpoint
3. **مستندات:** http://localhost:8000/docs
4. **مستندات کامل:** `API_DOCS.md`

---

**✅ اگر همه چیز کار کرد، آماده‌ای برای Frontend!** 🎉
