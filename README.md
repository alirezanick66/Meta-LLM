# File: README.md

# 🎨 Meta - سیستم پرسش و پاسخ هوشمند فارسی

سیستم RAG تخصصی برای پردازش مستندات شهرسازی و عمران با قابلیت جستجوی معنایی و کلیدواژه‌ای

## 🚀 ویژگی‌ها

- 🔍 Hybrid Retrieval (BM25 + Vector Search)
- 🤖 LLM با Groq و Gemini Fallback
- 🇮🇷 پشتیبانی کامل از زبان فارسی
- ⚡ Caching با Redis
- 📊 Reranking برای دقت بالاتر
- 🐳 Docker-based deployment

## 📋 پیش‌نیازها

- Docker & Docker Compose
- Python 3.11.9
- API Keys: Groq + Gemini

## ⚙️ نصب و راه‌اندازی

### 1. کلون پروژه
```bash
git clone <repository-url>
cd meta
```

### 2. تنظیم Environment Variables
فایل `.env` را ویرایش کنید و API Keys را وارد کنید:
```env
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```

### 3. اجرای Docker Compose
```bash
docker-compose up -d
```

### 4. چک کردن سلامت سرویس‌ها
```bash
# Backend health check
curl http://localhost:8000/health

# Qdrant health check
curl http://localhost:6333/health

# PostgreSQL check
docker exec meta_postgres pg_isready -U meta_user

# Redis check
docker exec meta_redis redis-cli ping
```

## 📚 API Documentation

پس از راه‌اندازی:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ معماری
```
Frontend (React) → Backend (FastAPI) → 
    ├── PostgreSQL (Metadata + Chunks)
    ├── Qdrant (Vector Store)
    ├── Redis (Cache)
    └── LLM (Groq/Gemini)
```

## 🔧 Development
```bash
# نصب dependencies محلی (اختیاری)
pip install -r requirements.txt

# اجرای backend به صورت محلی
cd backend
uvicorn app.main:app --reload
```

## 📝 License

MIT

## 👥 Contributors

Meta Team