# نظام الاجتماعات - Meeting System Documentation

## نظرة عامة - Overview

نظام الاجتماعات هو إضافة متكاملة لنظام إدارة التعلم تسمح للمستخدمين بإنشاء وإدارة اجتماعات من نوعين:
- اجتماعات عادية (وجهاً لوجه)
- اجتماعات عبر زووم (عن بعد)

The Meeting System is an integrated addition to the Learning Management System that allows users to create and manage two types of meetings:
- Normal meetings (face-to-face)
- Zoom meetings (remote)

## المميزات الرئيسية - Key Features

- إنشاء وتعديل وحذف الاجتماعات
- دعم اجتماعات زووم مع روابط زووم
- تسجيل الحضور والمغادرة
- حساب مدة الحضور تلقائياً
- نظام إشعارات متكامل (قبل يوم، قبل ساعة، إلغاء، إعادة جدولة)
- إرسال الإشعارات عبر البريد الإلكتروني
- عرض الاجتماعات القادمة والسابقة
- تصفية وبحث الاجتماعات

- Create, edit, and delete meetings
- Support for Zoom meetings with Zoom links
- Attendance and exit tracking
- Automatic attendance duration calculation
- Integrated notification system (day before, hour before, cancellation, rescheduling)
- Email notification delivery
- View upcoming and past meetings
- Filter and search meetings

## الصفحات والروابط - Pages and URLs

- `/meetings/` - قائمة جميع الاجتماعات (List all meetings)
- `/meetings/<id>/` - تفاصيل اجتماع معين (Meeting details)
- `/meetings/create/` - إنشاء اجتماع جديد (Create new meeting)
- `/meetings/<id>/update/` - تعديل اجتماع (Edit meeting)
- `/meetings/<id>/delete/` - حذف اجتماع (Delete meeting)
- `/my-meetings/` - اجتماعاتي (My meetings)
- `/meeting-notifications/` - إشعارات الاجتماعات (Meeting notifications)

## إعداد نظام الإشعارات - Setting Up Notifications

### إعدادات البريد الإلكتروني - Email Settings

تم إضافة إعدادات البريد الإلكتروني في ملف `settings.py`:

Email settings have been added to the `settings.py` file:

```python
# Base URL for absolute URLs (used in emails, etc.)
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@pdt.sa')
```

لاستخدام خدمة SMTP حقيقية، قم بتعديل المتغيرات البيئية أو تحديث القيم مباشرة في الملف.

To use a real SMTP service, modify the environment variables or update the values directly in the file.

### إعداد المهمة المجدولة - Setting Up Scheduled Task

تم إنشاء ملف `send_notifications.bat` لتشغيل أمر إرسال الإشعارات. لإعداد مهمة مجدولة في Windows:

A `send_notifications.bat` file has been created to run the notification sending command. To set up a scheduled task in Windows:

1. افتح "Task Scheduler" من لوحة التحكم (Open Task Scheduler from Control Panel)
2. انقر على "Create Basic Task" (Click on "Create Basic Task")
3. أدخل اسماً ووصفاً للمهمة (Enter a name and description for the task)
4. اختر متى تريد تشغيل المهمة (Choose when you want the task to run)
5. اختر "Start a program" (Choose "Start a program")
6. اختر ملف `send_notifications.bat` (Browse and select the `send_notifications.bat` file)
7. أكمل المعالج (Complete the wizard)

يُنصح بتشغيل المهمة كل 5 دقائق لضمان إرسال الإشعارات في الوقت المناسب.

It is recommended to run the task every 5 minutes to ensure timely notification delivery.

## أوامر الإدارة - Management Commands

تم إضافة أمر إدارة جديد لإرسال الإشعارات:

A new management command has been added for sending notifications:

```bash
python manage.py send_meeting_notifications
```

لإرسال جميع الإشعارات غير المرسلة بغض النظر عن وقت الجدولة:

To send all unsent notifications regardless of scheduled time:

```bash
python manage.py send_meeting_notifications --force
```

## نموذج البيانات - Data Models

### Meeting (الاجتماع)

- `title` - عنوان الاجتماع (Meeting title)
- `description` - وصف الاجتماع (Meeting description)
- `meeting_type` - نوع الاجتماع (NORMAL/ZOOM) (Meeting type)
- `start_time` - وقت بدء الاجتماع (Start time)
- `duration` - مدة الاجتماع (Duration)
- `school` - المدرسة المرتبطة (Associated school)
- `creator` - منشئ الاجتماع (Meeting creator)
- `zoom_link` - رابط زووم (إلزامي لاجتماعات زووم) (Zoom link - required for Zoom meetings)
- `recording_url` - رابط التسجيل (اختياري) (Recording URL - optional)
- `materials` - ملفات الاجتماع (اختياري) (Meeting materials - optional)
- `is_active` - حالة الاجتماع (نشط/ملغي) (Meeting status - active/cancelled)

### Participant (المشارك)

- `meeting` - الاجتماع المرتبط (Associated meeting)
- `user` - المستخدم (User)
- `attendance_time` - وقت الحضور (Attendance time)
- `exit_time` - وقت المغادرة (Exit time)
- `attendance_duration` - مدة الحضور (Attendance duration)

### Notification (الإشعار)

- `meeting` - الاجتماع المرتبط (Associated meeting)
- `notification_type` - نوع الإشعار (Notification type)
- `message` - نص الإشعار (Notification message)
- `recipients` - المستلمون (Recipients)
- `scheduled_time` - وقت الجدولة (Scheduled time)
- `sent` - حالة الإرسال (Sent status)
- `sent_at` - وقت الإرسال (Sent time)
- `is_read` - حالة القراءة (Read status)

## التخصيص - Customization

يمكن تخصيص النظام بسهولة من خلال:
- تعديل القوالب في `templates/website/meetings/`
- إضافة أنواع إشعارات جديدة في نموذج `Notification`
- تعديل طريقة إرسال الإشعارات في طريقة `send()` في نموذج `Notification`

The system can be easily customized by:
- Modifying templates in `templates/website/meetings/`
- Adding new notification types in the `Notification` model
- Modifying the notification sending method in the `send()` method of the `Notification` model
