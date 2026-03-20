# 🏗️ Meta - سیستم پرسش و پاسخ هوشمند فارسی

‫**سیستم RAG پیشرفته برای مستندات شهرسازی و عمران**

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com)
[![Status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](https://github.com)

---

## 📌 درباره پروژه

‫Meta یک سیستم پرسش و پاسخ هوشمند مبتنی بر RAG است که برای پاسخگویی به سوالات تخصصی در حوزه **شهرسازی و عمران** طراحی شده است.

|        مشخصات        |                     جزئیات                      |
| :------------------: | :---------------------------------------------: |
|        🎯 هدف        | پاسخ هوشمند به سوالات فارسی بر اساس مستندات فنی |
|  👥 کاربران همزمان   |            حداکثر 5 نفر (قابل Scale)            |
|     📊 حجم داده      |         ~1000 صفحه (~3000-4000 chunks)          |
| 📁 فرمت‌های پشتیبانی |          Markdown (.md), Word (.docx)           |
|   🖥️ محیط استقرار   |                       VPS                       |
|      🔐 دسترسی       |         دیتابیس مشترک برای همه کاربران          |

---

## ✨ ویژگی‌های کلیدی

‫**پردازش اسناد:**

- ✅ استخراج خودکار از Markdown و Word (.docx)
- ✅ نرمال‌سازی پیشرفته فارسی (بدون وابستگی به Hazm)
- ✅ Chunking هوشمند با Header Awareness
- ✅ تشخیص Duplicate با SHA-256 Hash

‫**جستجو و بازیابی:**

- ✅ جستجوی Hybrid (BM25 + Vector Semantic)
- ✅ Reciprocal Rank Fusion (RRF) برای ادغام نتایج
- ✅ BGE Reranker برای رتبه‌بندی نهایی
- ✅ Parallel Retrieval (45% سریع‌تر)

‫**هوش مصنوعی:**

- ✅ LLM Primary: Groq (llama-3.3-70b-versatile)
- ✅ LLM Fallback: Gemini (gemini-2.5-flash)
- ✅ Token Counting دقیق با gte-multilingual-base
- ✅ Prompt Builder بهینه با بودجه توکن کنترل‌شده

‫**رابط کاربری:**

- ✅ React 18 + Vite + Tailwind CSS
- ✅ تایپ افکت و Markdown Rendering
- ✅ نمایش منابع (Source Cards)
- ✅ پنل ادمین برای مدیریت اسناد

---

## 🚀 شروع سریع

‫**پیش‌نیازها:** Docker, Docker Compose, Python 3.10+, Node.js 18+

```bash
# کلون پروژه
git clone <repository-url>
cd Meta

# راه‌اندازی Backend
pip install -r backend/requirements.txt
docker-compose up -d
alembic upgrade head
uvicorn backend.app.main:app --reload

# راه‌اندازی Frontend
cd frontend && npm install && npm run dev
```

📖 **راهنمای کامل نصب:** [`DEVELOPMENT.md`](https://chat.qwen.ai/c/DEVELOPMENT.md)

## 📚 مستندات

|                              فایل                               |              توضیحات               |
| :-------------------------------------------------------------: | :--------------------------------: |
|      📋 [`ROADMAP.md`](https://chat.qwen.ai/c/ROADMAP.md)       | فازبندی پروژه و وضعیت انجام فازها  |
|  🛠️ [`DEVELOPMENT.md`](https://chat.qwen.ai/c/DEVELOPMENT.md)  |   راهنمای نصب، راه‌اندازی و تست    |
| 🏗️ [`ARCHITECTURE.md`](https://chat.qwen.ai/c/ARCHITECTURE.md) | معماری فنی، دیتابیس و ساختار پروژه |
|       📄 [`README.md`](https://chat.qwen.ai/c/README.md)        |      معرفی پروژه (همین فایل)       |

---

## 📊 وضعیت فعلی پروژه

|     فاز     |               عنوان               |      وضعیت      |
| :---------: | :-------------------------------: | :-------------: |
|  ✅ فاز 1-6  | Infrastructure تا LLM Integration |    تکمیل شده    |
| ✅ فاز 9-10  |       API Layer و Frontend        |    تکمیل شده    |
|   ⬜ فاز 7   |      Caching & Optimization       |  در دست اقدام   |
|   ⬜ فاز 8   |       Logging & Monitoring        | برنامه‌ریزی شده |
| ⬜ فاز 11-12 |  Advanced Features و Deployment   | برنامه‌ریزی شده |

‫📖 **جزئیات کامل فازها:** [`ROADMAP.md`](https://chat.qwen.ai/c/ROADMAP.md)

## 🔧 تکنولوژی‌های استفاده‌شده

|     لایه     |                     تکنولوژی                      |
| :----------: | :-----------------------------------------------: |
| **Backend**  |      FastAPI, Pydantic, SQLAlchemy, Alembic       |
| **Database** |             PostgreSQL, Qdrant, Redis             |
|  **AI/ML**   | gte-multilingual-base, BGE-Reranker, Groq, Gemini |
| **Frontend** |    React 18, Vite, Tailwind CSS, React Router     |
|  **DevOps**  |          Docker, Docker Compose, Loguru           |

---

**نسخه:** 1.4.0 | **آخرین بروزرسانی:** 2026-03-15