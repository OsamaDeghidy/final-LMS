# دليل إنشاء واستخدام الاجتماعات المباشرة
## How to Create and Use Live Meetings

## 📝 الخطوات لإنشاء غرفة اجتماع مباشر / Steps to Create Live Meeting Room

### 1️⃣ إنشاء اجتماع جديد / Create New Meeting

**للمدرسين والإداريين:**
1. اذهب إلى لوحة التحكم Dashboard
2. اختر "إدارة الاجتماعات" → "إنشاء اجتماع جديد"
3. أو اذهب مباشرة إلى: `http://127.0.0.1:8000/meetings/create/`

### 2️⃣ ملء بيانات الاجتماع / Fill Meeting Data

```
العنوان: اجتماع الرياضيات - الوحدة الأولى
الوصف: مراجعة الوحدة الأولى من مادة الرياضيات
النوع: ⭐ اختر "LIVE" (اجتماع مباشر) ⭐
تاريخ ووقت البداية: 2023-12-15 10:00 AM
المدة: 60 دقيقة
الحد الأقصى للمشاركين: 30
تفعيل الدردشة: ✅ نعم
تفعيل مشاركة الشاشة: ✅ نعم
تفعيل التسجيل: ✅ نعم (اختياري)
```

### 3️⃣ بدء الاجتماع المباشر / Start Live Meeting

**بعد إنشاء الاجتماع:**

1. **اذهب إلى تفاصيل الاجتماع:**
   ```
   http://127.0.0.1:8000/meetings/{meeting_id}/
   ```

2. **ستظهر لك الخيارات التالية حسب نوع المستخدم:**

   **للمنشئ (المدرس/الإداري):**
   ```
   🟢 زر "بدء الاجتماع المباشر" - إذا لم يبدأ بعد
   🔵 زر "دخول غرفة الاجتماع" - إذا بدأ الاجتماع
   🔴 زر "إنهاء الاجتماع" - لإنهاء الاجتماع
   ```

   **للطلاب:**
   ```
   ⏰ "لم يبدأ الاجتماع المباشر بعد" - إذا لم يبدأ
   🔵 زر "الانضمام للاجتماع المباشر" - للانضمام
   ⚠️ "تم الوصول للحد الأقصى" - إذا امتلأت الغرفة
   ✅ "انتهى الاجتماع المباشر" - إذا انتهى
   ```

### 4️⃣ دخول غرفة الاجتماع / Enter Meeting Room

**عند النقر على "الانضمام" أو "دخول غرفة الاجتماع":**

```
http://127.0.0.1:8000/meetings/{meeting_id}/live-room/
```

**ستظهر لك غرفة الاجتماع بالميزات التالية:**

## 🎥 ميزات غرفة الاجتماع المباشر / Live Meeting Room Features

### أ) منطقة الفيديو الرئيسية / Main Video Area
```
┌─────────────────────────────────┐
│        📹 منطقة الفيديو           │
│     (سيتم عرض الفيديوهات هنا)     │
│                                 │
│  🎤 🎥 🖥️ 🚪 (أدوات التحكم)    │
└─────────────────────────────────┘
```

### ب) أدوات التحكم / Meeting Controls
- **🎤 الميكروفون:** تشغيل/إيقاف الصوت
- **🎥 الكاميرا:** تشغيل/إيقاف الفيديو
- **🖥️ مشاركة الشاشة:** (إذا مفعلة)
- **🚪 المغادرة:** مغادرة الاجتماع

### ج) قائمة المشاركين / Participants Panel
```
👥 المشاركون (عدد المشاركين)
🟢 أحمد محمد (أنت)
🟢 سارة أحمد
🟢 محمد علي
```

### د) نظام الدردشة / Chat System
```
💬 الدردشة
─────────────────────
🤖 تم بدء الاجتماع المباشر
👤 أحمد: أهلاً بالجميع
👤 سارة: مرحباً
─────────────────────
[اكتب رسالة...] [إرسال]
```

## 🔄 تتبع الحضور التلقائي / Automatic Attendance Tracking

### يتم تسجيل الحضور تلقائياً:

1. **عند الدخول للغرفة:** يسجل وقت الدخول
2. **عند المغادرة:** يسجل وقت المغادرة
3. **حساب المدة:** يحسب إجمالي وقت الحضور

### في تفاصيل الاجتماع ستجد:
```
📊 معدل الحضور: 85%

جدول المشاركين:
─────────────────────────────────────
الاسم    | الحضور | وقت الدخول  | وقت المغادرة | المدة
─────────────────────────────────────
أحمد    | حاضر   | 10:05 AM   | 11:00 AM    | 55 دقيقة
سارة    | حاضر   | 10:10 AM   | 11:00 AM    | 50 دقيقة
محمد    | غائب   | -          | -           | -
```

## 🎯 سيناريو كامل / Complete Scenario

### مثال عملي لإنشاء واستخدام اجتماع مباشر:

```
1. المدرس ينشئ اجتماع نوع "LIVE" ✅
2. المدرس يذهب لتفاصيل الاجتماع ✅
3. المدرس ينقر "بدء الاجتماع المباشر" ✅
4. الطلاب يرون زر "الانضمام للاجتماع" ✅
5. الطلاب ينقرون للانضمام ✅
6. يتم تسجيل حضورهم تلقائياً ✅
7. يمكن للجميع استخدام الدردشة ✅
8. المدرس ينهي الاجتماع ✅
9. يتم حساب مدة حضور كل طالب ✅
```

## 🛠️ استكشاف الأخطاء / Troubleshooting

### مشاكل شائعة وحلولها:

| المشكلة | السبب | الحل |
|---------|-------|------|
| لا يظهر زر "بدء الاجتماع" | النوع ليس "LIVE" | تأكد من اختيار نوع LIVE |
| خطأ "غير مصرح" | ليس المنشئ | فقط منشئ الاجتماع يمكنه البدء |
| "تم الوصول للحد الأقصى" | الغرفة ممتلئة | انتظر مغادرة أحد المشاركين |
| الدردشة لا تعمل | غير مفعلة | تأكد من تفعيل الدردشة عند الإنشاء |

## 📱 الوصول عبر الروابط / Direct URL Access

```
الاجتماعات: http://127.0.0.1:8000/meetings/
إنشاء اجتماع: http://127.0.0.1:8000/meetings/create/
تفاصيل اجتماع: http://127.0.0.1:8000/meetings/{id}/
غرفة مباشرة: http://127.0.0.1:8000/meetings/{id}/live-room/
```

## ✨ ميزات إضافية / Additional Features

### التحديث التلقائي للدردشة:
- تحديث كل 3 ثوانٍ
- رسائل النظام (انضمام/مغادرة)
- حد أقصى 500 حرف للرسالة

### إشعارات Toastr:
- إشعار عند تسجيل الحضور
- إشعار عند بدء/إنهاء الاجتماع
- إشعارات الأخطاء

### الأمان:
- CSRF Protection لجميع العمليات
- فحص الصلاحيات لكل عملية
- تتبع حالة الاجتماع

---

## 🚀 البدء السريع / Quick Start

1. شغل الخادم: `python manage.py runserver`
2. اذهب إلى: `http://127.0.0.1:8000/meetings/create/`
3. أنشئ اجتماع نوع "LIVE"
4. ابدأ الاجتماع من صفحة التفاصيل
5. شارك الرابط مع الطلاب للانضمام

**الآن النظام جاهز للاستخدام! 🎉** 