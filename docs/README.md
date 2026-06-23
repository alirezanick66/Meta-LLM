## 🏗️MetaLLM

---

## 📌 درباره پروژه

متا  یک سیستم پرسش و پاسخ هوشمند مبتنی بر RAG است که برای پاسخگویی به سوالات تخصصی در حوزه **حقوق کار، تأمین اجتماعی و قوانین مرتبط** طراحی شده است

## 🎥 دمو ویدیویی

[🔗 مشاهده ویدیوی دمو](https://drive.google.com/file/d/1FcF3wSdqWhZ64Dr_o9iTt3lGOqJNlQrz/view?usp=sharing)


|        مشخصات        |                        جزئیات                         |
| :------------------: | :---------------------------------------------------: |
|        🎯 هدف        | پاسخ هوشمند به سوالات حقوقی فارسی بر اساس متون قانونی |
|  👥 کاربران همزمان   |               حداکثر 5 نفر (قابل Scale)               |
|     📊 حجم داده      |            ~1000 صفحه (~3000-4000 chunks)             |
| 📁 فرمت‌های پشتیبانی |             Markdown (.md), Word (.docx)              |
|   🖥️ محیط استقرار   |                          VPS                          |
|    📂 منابع داده     |               `docs/corpus`             |

---

## ✨ ویژگی‌های کلیدی

**پردازش اسناد:**

- ✅ استخراج خودکار از Markdown و Word (.docx)
- ✅ نرمال‌سازی پیشرفته فارسی (بدون وابستگی به Hazm)
- ✅ قابلیت Chunking هوشمند با Header Awareness
- ✅ تشخیص Duplicate با SHA-256 Hash

**جستجو و بازیابی:**

- ✅ جستجوی Hybrid (BM25 + Vector Semantic)
- ✅استفاده Reciprocal Rank Fusion (RRF) برای ادغام نتایج
- ✅ استفاده از GTE Multilingual Reranker برای رتبه‌بندی نهایی
- ✅ استفاده از Parallel Retrieval (~220ms، 45% سریع‌تر از Sequential)

**هوش مصنوعی:**

- ✅ LLM Primary: Groq — llama-3.3-70b-versatile
- ✅ LLM Fallback: Gemini — gemini-2.5-flash
- ✅ تشخیص خودکار سوالات سیستمی با Regex
- ✅ Prompt Builder با بودجه توکن کنترل‌شده

**رابط کاربری:**

- ✅ React 18 + Vite + Tailwind CSS
- ✅ Typing effect و Markdown Rendering
- ✅ نمایش منابع (Source Cards)
- ✅ پنل ادمین برای مدیریت اسناد

---

## 🔧 تکنولوژی‌ها

|     لایه     |                     تکنولوژی                      |
| :----------: | :-----------------------------------------------: |
| **Backend**  |      FastAPI, Pydantic, SQLAlchemy, Alembic       |
| **Database** |             PostgreSQL, Qdrant, Redis             |
|  **AI/ML**   | gte-multilingual-base, GTE-Reranker, Groq, Gemini |
| **Frontend** |    React 18, Vite, Tailwind CSS, React Router     |
|  **DevOps**  |          Docker, Docker Compose, Loguru           |

---

## 🚀 شروع سریع

**پیش‌نیازها:** Docker, Docker Compose, Python 3.10+, Node.js 18+

```bash
# راه‌اندازی Backend
pip install -r backend/requirements.txt
docker-compose up -d
alembic upgrade head
uvicorn backend.app.main:app --reload

# راه‌اندازی Frontend
cd frontend && npm install && npm run dev
```

📖 راهنمای کامل نصب: [`DEVELOPMENT.md`](DEVELOPMENT.md)

---

## 📚 مستندات

|                   فایل                   |                  توضیحات                  |
| :--------------------------------------: | :---------------------------------------: |
| 🏗️ [`ARCHITECTURE.md`](ARCHITECTURE.md) | معماری فنی، دیتابیس، Retrieval و لایه LLM |
|  🛠️ [`DEVELOPMENT.md`](DEVELOPMENT.md)  |       راهنمای نصب، راه‌اندازی و تست       |
|      🗺️ [`ROADMAP.md`](ROADMAP.md)      |     فازبندی پروژه و برنامه‌های آینده      |

---

## 📊 وضعیت فعلی

|    فاز    |               عنوان               |       وضعیت       |
| :-------: | :-------------------------------: | :---------------: |
|  فاز 1-6  | Infrastructure تا LLM Integration |      ✅ تکمیل      |
| فاز 9-10  |       API Layer و Frontend        |      ✅ تکمیل      |
|   فاز 7   |      Caching & Optimization       |      ⬜ بعدی       |
|   فاز 8   |       Logging & Monitoring        | ⬜ برنامه‌ریزی شده |
| فاز 11-12 |  Advanced Features و Deployment   | ⬜ برنامه‌ریزی شده |

📖 جزئیات کامل: [`ROADMAP.md`](ROADMAP.md)

---

> **نسخه:** 1.6.0 | **آخرین بروزرسانی:**  2026/03/22
