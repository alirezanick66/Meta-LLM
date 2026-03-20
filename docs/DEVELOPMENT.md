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
