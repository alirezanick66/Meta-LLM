# 🚀 راهنمای سریع - اجرای کامل پروژه Meta

این راهنما برای راه‌اندازی **سریع** Backend + Frontend.

---

## 📋 پیش‌نیازها

```bash
✅ Python 3.10+
✅ Node.js 18+
✅ Docker & Docker Compose
✅ Git
```

---

## 🎯 مراحل راه‌اندازی (5 دقیقه!)

### 1️⃣ Clone پروژه

```bash
git clone <repository-url>
cd meta-project
```

---

### 2️⃣ راه‌اندازی Docker Services

```bash
# PostgreSQL + Qdrant + Redis
docker-compose up -d

# بررسی وضعیت
docker-compose ps
```

باید ببینید:

```
✅ postgres    - Up
✅ qdrant      - Up
✅ redis       - Up (اختیاری)
```

---

### 3️⃣ راه‌اندازی Backend

#### نصب Dependencies:

```bash
cd backend

# ساخت virtual environment
python -m venv venv

# فعال‌سازی
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# نصب packages
pip install -r requirements.txt
```

#### تنظیمات `.env`:

```bash
# کپی کردن .env.example
cp .env.example .env

# ویرایش .env و اضافه کردن API Keys
# GROQ_API_KEY=your-key-here
# GEMINI_API_KEY=your-key-here
```

#### اجرای Backend:

```bash
# مهاجرت دیتابیس (اگر لازم باشد)
python -m backend.scripts.init_db

# اجرای سرور
uvicorn backend.app.main:app --reload
```

Backend روی `http://localhost:8000` در دسترس است.

---

### 4️⃣ راه‌اندازی Frontend

#### نصب Dependencies:

```bash
# در ترمینال جدید
cd frontend

npm install
```

#### اجرای Frontend:

```bash
npm run dev
```

Frontend روی `http://localhost:3000` در دسترس است.

---

## 🎉 تست کردن

### 1. باز کردن مرورگر:

```
http://localhost:3000
```

### 2. ارسال یک سوال:

```
"انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟"
```

### 3. دریافت پاسخ:

باید پاسخ + منابع رو ببینید! 🎊

---

## 📊 مشاهده Endpoints

### Swagger UI:

```
http://localhost:8000/docs
```

### Health Check:

```bash
curl http://localhost:8000/health
```

### Stats:

```bash
curl http://localhost:8000/api/stats
```

---

## 🐛 مشکلات متداول

### ❌ Backend اجرا نمیشه:

```bash
# بررسی Docker services
docker-compose ps

# بررسی لاگ‌ها
docker-compose logs postgres
docker-compose logs qdrant
```

### ❌ Frontend به Backend وصل نمیشه:

```bash
# بررسی Backend روی port 8000
curl http://localhost:8000/

# بررسی vite.config.js proxy settings
```

### ❌ خطای API Key:

```bash
# بررسی .env
cat backend/.env | grep API_KEY

# مطمئن شوید که API keys معتبر هستند
```

---

## 🛑 توقف سرویس‌ها

```bash
# توقف Docker
docker-compose down

# توقف Backend
# Ctrl+C در ترمینال Backend

# توقف Frontend
# Ctrl+C در ترمینال Frontend
```

---

## 📁 ساختار نهایی

```
meta-project/
├── backend/
│   ├── app/              # کد اصلی Backend
│   ├── data/             # داده‌ها و cache
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/              # کد اصلی Frontend
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## 🎯 مراحل بعدی

بعد از راه‌اندازی موفق:

1. ✅ اضافه کردن اسناد جدید:

```bash
python backend/scripts/upload_document.py path/to/file.md
```

2. ✅ تست کردن API:

```bash
python backend/scripts/test_api.py --verbose
```

3. ✅ مشاهده لاگ‌ها:

```bash
tail -f backend/logs/app.log
```

---

## 🎊 Done!

حالا پروژه شما آماده استفاده است! 🚀

**سوال دارید؟**

- 📚 مستندات: `/docs` در هر دو Backend و Frontend
- 🐛 Issues: GitHub Issues
- 💬 Support: پشتیبانی تیم

---

**موفق باشید!** 💪
