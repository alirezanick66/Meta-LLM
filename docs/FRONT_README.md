# 🎨 Meta Frontend

رابط کاربری سیستم پرسش و پاسخ هوشمند حقوقی متا

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
│   │   ├── ChatInterface.jsx     # کامپوننت اصلی چت
│   │   ├── Message.jsx           # نمایش پیام با Markdown
│   │   ├── InputBox.jsx          # فیلد ورودی
│   │   ├── MessageActions.jsx    # دکمه‌های Copy، Edit، Regenerate
│   │   ├── SkeletonMessage.jsx   # Loading state
│   │   ├── ScrollToBottom.jsx    # دکمه اسکرول به پایین
│   │   ├── SourceCards.jsx       # نمایش منابع collapsible
│   │   ├── SourceModal.jsx       # modal متن کامل chunk
│   │   ├── MarkdownRenderer.jsx  # رندر Markdown
│   │   └── admin/
│   │       ├── AdminLogin.jsx    # احراز هویت
│   │       ├── AdminPage.jsx     # صفحه مدیریت
│   │       ├── StatsCard.jsx     # نمایش آمار
│   │       ├── DocumentList.jsx  # لیست اسناد
│   │       └── UploadZone.jsx    # آپلود فایل
│   ├── constants/
│   │   └── questions.js          # سوالات نمونه حقوقی
│   ├── hooks/
│   │   └── useTypingEffect.js    # hook مدیریت typing
│   ├── pages/
│   │   ├── ChatPage.jsx          # صفحه چت
│   │   └── AdminPage.jsx         # صفحه ادمین
│   ├── services/
│   │   ├── api.js                # سرویس API (Axios)
│   │   └── adminApi.js           # سرویس API ادمین
│   ├── App.jsx                   # کامپوننت اصلی
│   ├── main.jsx                  # نقطه ورود
│   └── index.css                 # استایل‌های Tailwind
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## ✨ قابلیت‌ها

- 💬 رابط چت با Markdown rendering
- 📱 Responsive (موبایل + دسکتاپ)
- ↔️ RTL Support کامل
- ⚡ Skeleton loading state
- 📚 Source Cards با modal متن کامل
- 🔄 Auto-scroll با دکمه scroll to bottom
- ⌨️ Keyboard shortcuts (Enter/Shift+Enter)
- 📊 Character counter (حداکثر ۱۰۰۰)
- ✏️ ویرایش و ارسال مجدد پیام
- 🔁 Regenerate پاسخ
- 🎲 سوالات نمونه رندوم از ۵ حوزه حقوقی
- 🛡️ پنل ادمین با drag & drop upload

---

## 🎯 استفاده

### پیام ارسال:

1. متن خود را در فیلد ورودی تایپ کنید
2. `Enter` برای ارسال
3. `Shift + Enter` برای خط جدید

### مثال‌های سوال:

- «سهم کارگر از حق بیمه تأمین اجتماعی چند درصد است؟»
- «مدت مرخصی زایمان برای کارگران زن چقدر است؟»
- «حداقل مزد ماهانه سال ۱۴۰۴ چقدر است؟»

---

## 🔧 تنظیمات

### Vite Config (`vite.config.js`)

```js
server: {
  host: "127.0.0.1",
  port: 3000,
  strictPort: true,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

## 📝 Scripts

```bash
npm run dev      # اجرای development server
npm run build    # Build برای production
npm run preview  # پیش‌نمایش build شده
```

---

## 🎨 طراحی

### رنگ‌ها (Light Theme):

- Background: `#ffffff`
- پیام کاربر: `#fff6d9` (زرد روشن)
- پیام ربات: بدون background
- دکمه ارسال: `#ffc414` (زرد طلایی)
- Accent: `#10a37f` (سبز)

### فونت:

- **Mikhak** برای فارسی

---

## 🐛 Troubleshooting

### سرور پاسخ نمی‌دهد:

```bash
uvicorn backend.app.main:app --reload
```

### Proxy کار نمی‌کند:

مطمئن شوید `vite.config.js` صحیح تنظیم شده است.

---

## 🛡️ پنل ادمین

- دسترسی: `/admin`
- قابلیت‌ها: آپلود سند، مشاهده آمار، حذف اسناد

---

## 🙏 نکات مهم

- ✅ Backend را قبل از Frontend اجرا کنید
- ✅ Port های 3000 و 8000 باید آزاد باشند
- ✅ Node.js نسخه 18+ نیاز است


> **نسخه:** 1.1.0 | **آخرین بروزرسانی:**  2026/03/22
