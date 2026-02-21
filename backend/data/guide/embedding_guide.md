# 🎯 Embedding Service - راهنمای استفاده

## 📖 معرفی

`EmbeddingService` یک سرویس کامل برای ساخت embeddings با مدل **BGE-M3** است.

### ویژگی‌ها:
- ✅ پشتیبانی از single و batch embedding
- ✅ بهینه‌سازی برای CPU
- ✅ مدیریت خودکار حافظه
- ✅ Singleton pattern (مدل یک بار load میشه)
- ✅ محاسبه similarity

---

## 🚀 نحوه استفاده

### 1️⃣ Import:

```python
from backend.app.services.embedding_service import embedding_service
```

---

### 2️⃣ ساخت embedding برای یک متن:

```python
text = "انقلاب اسلامی ایران"
embedding = embedding_service.embed_single(text)

print(embedding.shape)  # (1024,)
```

---

### 3️⃣ ساخت embedding برای چند متن (batch):

```python
texts = [
    "متن اول",
    "متن دوم", 
    "متن سوم"
]

embeddings = embedding_service.embed_batch(texts)
# خروجی: لیستی از numpy arrays
```

---

### 4️⃣ ساخت embedding برای chunks:

```python
chunks = [
    {"chunk_id": "001", "content": "محتوای chunk اول"},
    {"chunk_id": "002", "content": "محتوای chunk دوم"},
]

# embedding به هر chunk اضافه میشه
chunks_with_embeddings = embedding_service.embed_chunks(chunks)

# حالا هر chunk فیلد 'embedding' داره:
print(chunks_with_embeddings[0]['embedding'])
```

---

### 5️⃣ محاسبه similarity:

```python
emb1 = embedding_service.embed_single("انقلاب")
emb2 = embedding_service.embed_single("انقلاب اسلامی")

similarity = embedding_service.calculate_similarity(emb1, emb2)
print(f"Similarity: {similarity:.4f}")  # مثلاً 0.8523
```

---

## ⚙️ تنظیمات

تنظیمات از `config.py` خوانده میشه:

```python
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DEVICE = "cpu"  # یا "cuda"
EMBEDDING_BATCH_SIZE = 32
```

---

## 📊 مشخصات مدل BGE-M3

| ویژگی | مقدار |
|-------|-------|
| **Model** | BAAI/bge-m3 |
| **Output Dimension** | 1024 |
| **Max Sequence Length** | 8192 tokens |
| **زبان** | پشتیبانی از 100+ زبان (شامل فارسی) |
| **بهینه برای** | Semantic search, RAG |

---

## 🎯 نکات مهم

### 1. Normalization:
```python
# برای cosine similarity همیشه normalize کن:
embedding = embedding_service.embed_single(text, normalize=True)
```

### 2. Batch Processing:
```python
# برای متن‌های زیاد، batch استفاده کن (سریع‌تره):
embeddings = embedding_service.embed_batch(texts)  # ✅ بهتر
# vs
embeddings = [embed_single(t) for t in texts]  # ❌ کندتر
```

### 3. Memory Management:
```python
# Singleton pattern: مدل یک بار load میشه
service1 = get_embedding_service()  # load مدل
service2 = get_embedding_service()  # همون instance قبلی ✅
```

---

## 🧪 تست

برای تست سرویس:

```bash
python scripts/test_embedding_service.py
```

---

## 📝 TODO (برای بعد)

- [ ] اضافه کردن caching (Redis)
- [ ] پشتیبانی از GPU batch optimization
- [ ] Quantization برای سرعت بیشتر
- [ ] Monitoring و metrics

---

## 🐛 رفع مشکلات رایج

### مشکل: "CUDA out of memory"
```python
# راه حل: کاهش batch size
EMBEDDING_BATCH_SIZE = 16  # به جای 32
```

### مشکل: "Model loading is slow"
```python
# راه حل: مدل یک بار load میشه (Singleton)
# بار اول کند است، بار‌های بعدی فوری
```

### مشکل: "Dimension mismatch"
```python
# مدل خودش dimension رو تشخیص میده
# اگه تغییر کرد، warning میده
```