# 🎨 Meta Frontend - MVP

یک رابط کاربری مدرن و ساده برای سیستم پرسش و پاسخ هوشمند Meta.

---

## 🚀 راه‌اندازی سریع

### 1️⃣ نصب Dependencies:

```bash
cd frontend
npm install
```

### 2️⃣ اجرای Development Server:

```bash
npm run dev
```

سرور روی `http://localhost:3000` اجرا می‌شود.

---

## 📦 ساختار پروژه

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx    # کامپوننت اصلی چت
│   │   ├── Message.jsx           # نمایش یک پیام
│   │   └── InputBox.jsx          # فیلد ورودی
│   ├── services/
│   │   └── api.js                # سرویس API (Axios)
│   ├── App.jsx                   # کامپوننت اصلی
│   ├── main.jsx                  # نقطه ورود
│   └── index.css                 # استایل‌های Tailwind
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## ✨ قابلیت‌های MVP

### ✅ پیاده‌سازی شده:

- 💬 رابط چت ساده و زیبا
- 📱 Responsive (موبایل + دسکتاپ)
- 🎨 Dark Theme
- ↔️ RTL Support کامل
- ⚡ Loading states
- 📚 نمایش منابع (Sources)
- 🔄 Auto-scroll
- ⌨️ Keyboard shortcuts (Enter/Shift+Enter)
- 📊 Character counter
- ❌ Error handling

### 🔜 برای آینده:

- 📝 History + Sidebar
- 🎯 Source Cards با Modal
- ⚙️ Settings Panel
- 🎙️ Voice Input
- ✨ Advanced Animations
- 📝 Markdown Rendering

---

## 🎯 استفاده

### پیام ارسال:

1. متن خود را در فیلد ورودی تایپ کنید
2. `Enter` برای ارسال
3. `Shift + Enter` برای خط جدید

### مثال‌های سوال:

- "انقلاب اسلامی چه تأثیری داشت؟"
- "ویژگی‌های انقلاب اسلامی چیست؟"
- "نقش امام خمینی در انقلاب"

---

## 🔧 تنظیمات

### Vite Config (`vite.config.js`)

```js
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

### Tailwind Config (`tailwind.config.js`)

رنگ‌ها و تم سفارشی در اینجا تعریف شده‌اند.

---

## 📝 Scripts

```bash
# اجرای development server
npm run dev

# Build برای production
npm run build

# پیش‌نمایش build شده
npm run preview
```

---

## 🎨 طراحی

### رنگ‌ها (Dark Theme):

- Background: `#212121`
- Secondary: `#2f2f2f`
- User Message: `#2f4f4f`
- Bot Message: `#1e1e1e`
- Accent: `#10a37f` (سبز)

### فونت:

- **Vazirmatn** برای فارسی
- **Inter** برای انگلیسی

---

## 🐛 Troubleshooting

### سرور پاسخ نمی‌دهد:

```bash
# بررسی کنید که Backend روی port 8000 در حال اجراست
cd backend
uvicorn backend.app.main:app --reload
```

### خطای CORS:

Backend باید `allow_origins=["*"]` داشته باشد (در `main.py`).

### Proxy کار نمی‌کند:

مطمئن شوید که `vite.config.js` صحیح تنظیم شده است.

---

## 🎉 تست کردن

1. Backend را اجرا کنید:

```bash
cd backend
uvicorn backend.app.main:app --reload
```

2. Frontend را اجرا کنید:

```bash
cd frontend
npm run dev
```

3. مرورگر را باز کنید: `http://localhost:3000`

4. یک سوال بپرسید و پاسخ دریافت کنید! 🚀

---

## 📸 Screenshot

```
┌─────────────────────────────────────┐
│  🤖 Meta - دستیار هوشمند شهرسازی   │
├─────────────────────────────────────┤
│                                     │
│  👤 شما:                            │
│  انقلاب اسلامی چه تأثیری...        │
│                                     │
│  🤖 Meta:                           │
│  انقلاب اسلامی تأثیرات عمیقی...   │
│                                     │
│  📚 منابع:                         │
│  [1] enghelab.md                   │
│                                     │
├─────────────────────────────────────┤
│  💬 پیام خود را بنویسید...   [➤] │
└─────────────────────────────────────┘
```

---

## 🙏 نکات مهم

- ✅ حتماً Backend را قبل از Frontend اجرا کنید
- ✅ Port های 3000 و 8000 باید آزاد باشند
- ✅ Node.js نسخه 18+ نیاز است
- ✅ npm نسخه 9+ توصیه می‌شود

---

**ساخته شده با ❤️ برای پروژه Meta**
