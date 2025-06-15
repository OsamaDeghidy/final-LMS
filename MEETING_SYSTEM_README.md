# نظام الاجتماعات المدمج - Integrated Meeting System

## نظرة عامة

نظام اجتماعات مدمج متطور يوفر تجربة اجتماعات تفاعلية داخل منصة إدارة التعلم مع تتبع حضور تلقائي ودردشة مدمجة.

## الميزات الرئيسية

### 🎯 أنواع الاجتماعات
- **اجتماع عادي**: اجتماع بسيط للمناقشات
- **اجتماع زووم**: تكامل مع Zoom للاجتماعات الخارجية  
- **اجتماع مباشر**: اجتماع مدمج كاملاً داخل النظام

### 📊 تتبع الحضور التلقائي
- تسجيل وقت الانضمام تلقائياً
- تسجيل وقت المغادرة تلقائياً
- حساب مدة الحضور الكاملة
- تقارير مفصلة عن معدل الحضور

### 💬 نظام دردشة متقدم
- دردشة نصية فورية
- رسائل نظام للإشعارات
- تحديث تلقائي للرسائل
- حفظ سجل كامل للمحادثات

### 🎛️ أدوات تحكم شاملة
- تحكم في الميكروفون
- تحكم في الكاميرا
- مشاركة الشاشة (اختيارية)
- إدارة المشاركين

## متطلبات النظام

### متطلبات البرمجيات
- Python 3.8+
- Django 4.0+
- jQuery 3.6+
- Bootstrap 5.0+
- Font Awesome 5.15+

### قاعدة البيانات
- PostgreSQL (مفضل)
- MySQL
- SQLite (للتطوير)

## التثبيت والإعداد

### 1. إعداد قاعدة البيانات
```bash
# تطبيق التحديثات على قاعدة البيانات
python manage.py makemigrations
python manage.py migrate
```

### 2. إعداد الملفات الثابتة
```bash
# جمع الملفات الثابتة
python manage.py collectstatic
```

### 3. إعداد المتغيرات
```python
# في settings.py
MEETING_SETTINGS = {
    'MAX_PARTICIPANTS_DEFAULT': 50,
    'MAX_PARTICIPANTS_LIMIT': 200,
    'CHAT_MESSAGE_MAX_LENGTH': 500,
    'AUTO_MARK_EXIT_ON_LEAVE': True,
    'CHAT_REFRESH_INTERVAL': 3000,  # بالملليثانية
}
```

## دليل الاستخدام

### للمعلمين - إنشاء اجتماع مباشر

1. **إنشاء الاجتماع**
   - انتقل إلى "الاجتماعات" → "إنشاء اجتماع جديد"
   - اختر "اجتماع مباشر" كنوع الاجتماع
   - املأ البيانات المطلوبة (العنوان، الوصف، الوقت)
   - حدد إعدادات الاجتماع:
     - الحد الأقصى للمشاركين (2-200)
     - تمكين الدردشة
     - تمكين مشاركة الشاشة
     - تمكين التسجيل (مستقبلياً)

2. **بدء الاجتماع**
   - في صفحة تفاصيل الاجتماع، اضغط "بدء الاجتماع المباشر"
   - سيتم إنشاء غرفة اجتماع فريدة
   - شارك رابط الاجتماع مع الطلاب

3. **إدارة الاجتماع**
   - راقب قائمة المشاركين في الوقت الفعلي
   - استخدم نظام الدردشة للتواصل
   - اضغط "إنهاء الاجتماع" عند الانتهاء

### للطلاب - الانضمام للاجتماع

1. **الانضمام**
   - انتقل إلى صفحة تفاصيل الاجتماع
   - اضغط "الانضمام للاجتماع المباشر"
   - سيتم تسجيل حضورك تلقائياً

2. **أثناء الاجتماع**
   - استخدم أدوات التحكم في الأسفل
   - شارك في الدردشة إذا كانت مفعلة
   - اضغط "مغادرة الاجتماع" عند الانتهاء

## الصلاحيات والأمان

### صلاحيات المعلمين
- إنشاء وتعديل الاجتماعات
- بدء وإنهاء الاجتماعات المباشرة
- عرض تقارير الحضور التفصيلية
- إدارة إعدادات الاجتماع

### صلاحيات الطلاب
- عرض قائمة الاجتماعات
- الانضمام للاجتماعات المتاحة
- المشاركة في الدردشة
- عرض سجل حضورهم الشخصي

### إجراءات الأمان
- التحقق من صلاحيات المستخدم
- التحقق من حالة الاجتماع قبل الانضمام
- حماية من إرسال رسائل فارغة أو طويلة
- تنظيف البيانات المدخلة

## واجهة برمجة التطبيقات (API)

### نقاط الوصول الرئيسية

```python
# بدء اجتماع مباشر
POST /meetings/{id}/start-live/
Response: {"status": "success", "room_id": "uuid", "message": "تم بدء الاجتماع"}

# إنهاء اجتماع مباشر  
POST /meetings/{id}/end-live/
Response: {"status": "success", "message": "تم إنهاء الاجتماع"}

# إرسال رسالة دردشة
POST /meetings/{id}/send-chat/
Data: {"message": "نص الرسالة"}
Response: {"status": "success", "message_id": 123}

# جلب رسائل الدردشة
GET /meetings/{id}/get-chat/
Response: {"status": "success", "messages": [...]}

# تسجيل الحضور
POST /meetings/{id}/mark-attendance/
Response: {"status": "success", "attendance_time": "2024-01-01 10:00:00"}

# تسجيل المغادرة
POST /meetings/{id}/mark-exit/
Response: {"status": "success", "exit_time": "2024-01-01 11:00:00"}
```

## الهيكل التقني

### نماذج البيانات

```python
# نموذج الاجتماع
class Meeting(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    meeting_type = models.CharField(choices=MEETING_TYPES)
    start_time = models.DateTimeField()
    duration = models.DurationField()
    creator = models.ForeignKey(User)
    
    # حقول الاجتماع المباشر
    meeting_room_id = models.CharField(max_length=255)
    is_live_started = models.BooleanField(default=False)
    live_started_at = models.DateTimeField()
    live_ended_at = models.DateTimeField()
    max_participants = models.IntegerField(default=50)
    enable_screen_share = models.BooleanField(default=True)
    enable_chat = models.BooleanField(default=True)
    enable_recording = models.BooleanField(default=False)

# نموذج المشارك
class Participant(models.Model):
    meeting = models.ForeignKey(Meeting)
    user = models.ForeignKey(User)
    is_attending = models.BooleanField(default=False)
    attendance_time = models.DateTimeField()
    exit_time = models.DateTimeField()
    attendance_duration = models.DurationField()

# نموذج دردشة الاجتماع
class MeetingChat(models.Model):
    meeting = models.ForeignKey(Meeting, related_name='chat_messages')
    user = models.ForeignKey(User)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False)
```

### العروض (Views)

```python
# العروض الرئيسية
meeting_list         # قائمة الاجتماعات
meeting_detail       # تفاصيل الاجتماع
meeting_create       # إنشاء اجتماع
meeting_update       # تعديل اجتماع
meeting_delete       # حذف اجتماع

# عروض الاجتماع المباشر
meeting_live_room    # غرفة الاجتماع المباشر
start_live_meeting   # بدء الاجتماع المباشر
end_live_meeting     # إنهاء الاجتماع المباشر
send_chat_message    # إرسال رسالة دردشة
get_chat_messages    # جلب رسائل الدردشة

# عروض الحضور
mark_attendance      # تسجيل الحضور
mark_exit           # تسجيل المغادرة
```

## التخصيص والتطوير

### إضافة ميزات جديدة

1. **تكامل WebRTC للفيديو**
```javascript
// مثال لإضافة WebRTC
navigator.mediaDevices.getUserMedia({video: true, audio: true})
    .then(stream => {
        // إعداد اتصال الفيديو
    });
```

2. **تسجيل الاجتماعات**
```python
# إضافة حقل للتسجيل
class Meeting(models.Model):
    recording_file = models.FileField(upload_to='recordings/')
    is_recording = models.BooleanField(default=False)
```

3. **تحليلات متقدمة**
```python
# إضافة نموذج للتحليلات
class MeetingAnalytics(models.Model):
    meeting = models.OneToOneField(Meeting)
    total_participants = models.IntegerField()
    average_attendance_duration = models.DurationField()
    peak_participants_count = models.IntegerField()
    chat_messages_count = models.IntegerField()
```

### إعدادات التخصيص

```python
# في settings.py
MEETING_CUSTOMIZATION = {
    'THEME_COLOR': '#007bff',
    'CUSTOM_LOGO': 'path/to/logo.png',
    'ENABLE_SCREEN_SHARING': True,
    'ENABLE_CHAT_EMOJIS': True,
    'ENABLE_FILE_SHARING': False,
    'ENABLE_BREAKOUT_ROOMS': False,
}
```

## استكشاف الأخطاء

### مشاكل شائعة وحلولها

1. **لا يتم تسجيل الحضور**
   - تحقق من تسجيل دخول المستخدم
   - تأكد من بدء الاجتماع
   - تحقق من صلاحيات المستخدم

2. **الدردشة لا تعمل**
   - تأكد من تمكين الدردشة في إعدادات الاجتماع
   - تحقق من كون المستخدم مشارك في الاجتماع
   - تأكد من عمل JavaScript

3. **مشاكل في الأداء**
   - قلل فترة تحديث الدردشة
   - استخدم قاعدة بيانات محسنة
   - أضف فهرسة للجداول

### سجلات الأخطاء

```python
# في settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'meeting_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/meetings.log',
        },
    },
    'loggers': {
        'website.meeting_views': {
            'handlers': ['meeting_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## الدعم والمساهمة

### الحصول على المساعدة
- راجع الوثائق أولاً
- ابحث في الأخطاء الشائعة
- تواصل مع فريق الدعم التقني

### المساهمة في التطوير
1. Fork المشروع
2. أنشئ branch جديد للميزة
3. اكتب اختبارات للكود الجديد
4. أرسل Pull Request

### تقرير الأخطاء
- استخدم نموذج تقرير الأخطاء
- أرفق سجلات الأخطاء
- اذكر خطوات إعادة إنتاج المشكلة

## الترخيص

هذا النظام مطور كجزء من منصة إدارة التعلم وهو خاضع لنفس شروط الترخيص الخاصة بالمنصة الأساسية.

---

## إصدارات النظام

### الإصدار 1.0.0 (الحالي)
- نظام اجتماعات مباشرة أساسي
- تتبع حضور تلقائي
- دردشة مدمجة
- أدوات تحكم أساسية

### خارطة طريق الإصدارات القادمة

#### الإصدار 1.1.0 (قريباً)
- تكامل WebRTC للفيديو والصوت
- تحسينات في الأداء
- تقارير حضور متقدمة

#### الإصدار 1.2.0 (مستقبلي)
- تسجيل الاجتماعات
- مشاركة الملفات
- تقسيم إلى مجموعات صغيرة

#### الإصدار 2.0.0 (رؤية مستقبلية)
- ذكاء اصطناعي للتحليلات
- تكامل مع منصات خارجية متعددة
- تطبيق موبايل مصاحب
