# 📡 API Documentation - Meta

## 🚀 راه‌اندازی سریع

### 1. نصب Dependencies

```bash
pip install -r requirements.txt
```

### 2. راه‌اندازی Docker Services

```bash
docker-compose up -d
```

### 3. اجرای Migrations

```bash
alembic upgrade head
```

### 4. Indexing اولیه (در صورت نیاز)

```bash
python scripts/test_full_indexing.py
```

### 5. اجرای API Server

```bash
# Development (با hot-reload)
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📌 Endpoints

### Base URL

```
http://localhost:8000
```

### Interactive Docs

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🔵 Core Endpoints

### 1️⃣ **Root Endpoint**

```http
GET /
```

**Response:**

```json
{
	"message": "به Meta API خوش آمدید",
	"status": "running",
	"version": "1.0.0",
	"docs": "/docs",
	"endpoints": {
		"chat": "/api/chat",
		"stats": "/api/stats",
		"health": "/health"
	}
}
```

---

### 2️⃣ **Health Check**

```http
GET /health
```

**Response:**

```json
{
	"status": "healthy",
	"service": "Meta API",
	"postgres": "connected",
	"qdrant": "connected",
	"qdrant_vectors": 68
}
```

---

### 3️⃣ **System Stats**

```http
GET /api/stats
```

**Response:**

```json
{
	"total_documents": 1,
	"total_chunks": 68,
	"qdrant_vectors": 68,
	"bm25_chunks": 68,
	"embedding_model": "BAAI/bge-m3",
	"llm_primary": "groq: llama-3.3-70b-versatile",
	"timestamp": "2026-02-15T10:30:00Z"
}
```

---

### 4️⃣ **Chat Endpoint** ⭐

```http
POST /api/chat
```

**Request Body:**

```json
{
	"query": "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟",
	"temperature": 0.3
}
```

**Parameters:**

- `query` (required): سوال کاربر (1-1000 کاراکتر)
- `temperature` (optional): میزان خلاقیت پاسخ (0.0-2.0، default: از config)

**Response (Success):**

```json
{
	"success": true,
	"answer": "انقلاب اسلامی تأثیرات عمیقی بر نظریه‌های غربی گذاشت...",
	"sources": [
		{
			"index": 1,
			"chunk_id": "doc_1_chunk_003",
			"source": "enghelab.md",
			"hierarchy": "انقلاب اسلامی > تأثیرات"
		}
	],
	"metadata": {
		"provider": "groq",
		"model": "llama-3.3-70b-versatile",
		"usage": {
			"prompt_tokens": 2847,
			"completion_tokens": 309,
			"total_tokens": 3156
		},
		"is_system_question": false,
		"retrieval_count": 5,
		"response_time": 2.45
	},
	"error": null,
	"timestamp": "2026-02-15T10:30:00Z"
}
```

**Response (Error):**

```json
{
	"success": false,
	"answer": null,
	"sources": [],
	"metadata": null,
	"error": "متأسفانه در اسناد موجود، اطلاعاتی مرتبط با سوال شما پیدا نشد.",
	"timestamp": "2026-02-15T10:30:00Z"
}
```

---

## 📝 Example Requests

### cURL

```bash
# Chat Request
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ویژگی‌های انقلاب اسلامی چیست؟",
    "temperature": 0.3
  }'

# Health Check
curl -X GET "http://localhost:8000/health"

# Stats
curl -X GET "http://localhost:8000/api/stats"
```

### Python (requests)

```python
import requests

# Chat
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "query": "نقش امام خمینی در انقلاب چه بود؟",
        "temperature": 0.3
    }
)
print(response.json())

# Stats
stats = requests.get("http://localhost:8000/api/stats").json()
print(f"Documents: {stats['total_documents']}")
```

### JavaScript (fetch)

```javascript
// Chat
const response = await fetch("http://localhost:8000/api/chat", {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({
		query: "انقلاب اسلامی چگونه رخ داد؟",
		temperature: 0.3,
	}),
});

const data = await response.json();
console.log(data.answer);
```

---

## ⚠️ Error Handling

### HTTP Status Codes

- `200` - موفقیت
- `422` - خطای validation (ورودی نامعتبر)
- `500` - خطای داخلی سرور
- `503` - سرویس در دسترس نیست (مشکل دیتابیس/Qdrant)
- `504` - Timeout

### Error Response Format

```json
{
	"success": false,
	"error": "توضیح خطا به فارسی",
	"details": null
}
```

### Common Errors

#### 1. Validation Error (422)

```json
{
  "success": false,
  "error": "خطا در فیلد 'query': سوال نمی‌تواند خالی باشد",
  "details": [...]
}
```

#### 2. No Results Found

```json
{
	"success": false,
	"error": "متأسفانه در اسناد موجود، اطلاعاتی مرتبط با سوال شما پیدا نشد."
}
```

#### 3. LLM Error

```json
{
	"success": false,
	"error": "خطا در تولید پاسخ. لطفاً دوباره تلاش کنید."
}
```

---

## 🧪 تست API

### اجرای تست‌های خودکار

```bash
python scripts/test_api.py
```

### تست دستی با Swagger UI

1. مرورگر را باز کنید: http://localhost:8000/docs
2. روی `/api/chat` کلیک کنید
3. "Try it out" را بزنید
4. Request body را پر کنید
5. "Execute" بزنید

---

## 🔧 Configuration

تنظیمات در فایل `.env`:

```env
# LLM Settings
LLM_PRIMARY=groq
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-2.0-flash-exp
TEMPERATURE=0.3
MAX_TOKENS=2048

# Retrieval Settings
BM25_TOP_K=20
VECTOR_TOP_K=20
RERANKER_TOP_K=5

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
```

---

## 📊 Performance Tips

### 1. بهینه‌سازی تعداد Workers

```bash
# CPU-bound: workers = (2 * CPU_cores) + 1
uvicorn backend.app.main:app --workers 9
```

### 2. استفاده از Gunicorn

```bash
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 3. Timeout Settings

```python
# در client
requests.post(url, json=data, timeout=30)
```

---

## 🚦 Rate Limiting

⚠️ **فعلاً غیرفعال است** (فاز 7)

در آینده اضافه خواهد شد:

- محدودیت: 100 request/min per IP
- Header: `X-RateLimit-Remaining`

---

## 🔐 Security

### CORS

فعلاً تمام origin ها مجاز هستند (`allow_origins=["*"]`)

⚠️ **در production باید محدود شود:**

```python
allow_origins=[
    "http://localhost:3000",
    "https://yourdomain.com"
]
```

### API Key (فاز بعد)

در نسخه‌های آینده authentication اضافه خواهد شد.

---

## 📞 Support

در صورت مشکل:

1. لاگ‌ها را بررسی کنید: `backend/data/logs/`
2. Health check را تست کنید: `/health`
3. Docker services را چک کنید: `docker-compose ps`

---

**ساخته شده با ❤️ برای پاسخگویی هوشمند**
