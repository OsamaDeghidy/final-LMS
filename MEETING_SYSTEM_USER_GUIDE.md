# دليل استخدام نظام الاجتماعات - Meeting System User Guide

## مقدمة - Introduction

نظام الاجتماعات هو نظام متكامل لإدارة الاجتماعات في منصة إدارة التعلم. يتيح النظام للمستخدمين إنشاء وإدارة الاجتماعات، وتتبع الحضور، وإرسال الإشعارات التلقائية.

The Meeting System is an integrated system for managing meetings in the Learning Management Platform. It allows users to create and manage meetings, track attendance, and send automatic notifications.

## الميزات الرئيسية - Main Features

### 1. إدارة الاجتماعات - Meeting Management

#### إنشاء اجتماع جديد - Creating a New Meeting

1. انتقل إلى صفحة "الاجتماعات" من القائمة الرئيسية.
2. انقر على زر "إنشاء اجتماع جديد".
3. املأ النموذج بالمعلومات المطلوبة:
   - عنوان الاجتماع
   - وصف الاجتماع
   - نوع الاجتماع (عادي أو زووم)
   - وقت البدء
   - المدة (بالدقائق)
   - المدرسة
   - رابط زووم (إذا كان نوع الاجتماع زووم)
   - المواد (اختياري)
4. انقر على "حفظ" لإنشاء الاجتماع.

1. Navigate to the "Meetings" page from the main menu.
2. Click on the "Create New Meeting" button.
3. Fill out the form with the required information:
   - Meeting title
   - Meeting description
   - Meeting type (Normal or Zoom)
   - Start time
   - Duration (in minutes)
   - School
   - Zoom link (if meeting type is Zoom)
   - Materials (optional)
4. Click "Save" to create the meeting.

#### تعديل اجتماع - Editing a Meeting

1. انتقل إلى صفحة تفاصيل الاجتماع.
2. انقر على زر "تعديل".
3. قم بتحديث المعلومات المطلوبة.
4. انقر على "حفظ" لتحديث الاجتماع.

1. Navigate to the meeting details page.
2. Click on the "Edit" button.
3. Update the required information.
4. Click "Save" to update the meeting.

#### حذف اجتماع - Deleting a Meeting

1. انتقل إلى صفحة تفاصيل الاجتماع.
2. انقر على زر "حذف".
3. قم بتأكيد الحذف.

1. Navigate to the meeting details page.
2. Click on the "Delete" button.
3. Confirm the deletion.

### 2. تسجيل الحضور - Attendance Tracking

#### تسجيل الحضور - Marking Attendance

1. انتقل إلى صفحة تفاصيل الاجتماع.
2. انقر على زر "تسجيل الحضور" لتسجيل حضورك.
3. عند المغادرة، انقر على زر "تسجيل المغادرة".

1. Navigate to the meeting details page.
2. Click on the "Mark Attendance" button to record your attendance.
3. When leaving, click on the "Mark Exit" button.

#### عرض سجل الحضور - Viewing Attendance Records

1. انتقل إلى صفحة تفاصيل الاجتماع.
2. انتقل إلى قسم "سجل الحضور" لعرض قائمة الحاضرين ومدة حضورهم.

1. Navigate to the meeting details page.
2. Go to the "Attendance Record" section to view the list of attendees and their attendance duration.

### 3. نظام الإشعارات - Notification System

#### عرض الإشعارات - Viewing Notifications

1. انقر على رابط "إشعارات الاجتماعات" من القائمة الرئيسية.
2. ستظهر قائمة بجميع الإشعارات المرسلة إليك.
3. يمكنك تصفية الإشعارات حسب حالة القراءة (مقروءة/غير مقروءة).

1. Click on the "Meeting Notifications" link from the main menu.
2. A list of all notifications sent to you will appear.
3. You can filter notifications by read status (read/unread).

#### تمييز الإشعارات كمقروءة - Marking Notifications as Read

1. انتقل إلى صفحة الإشعارات.
2. انقر على زر "تمييز كمقروءة" بجانب الإشعار الذي تريد تمييزه كمقروء.

1. Navigate to the notifications page.
2. Click on the "Mark as Read" button next to the notification you want to mark as read.

### 4. لوحة التحكم - Dashboard

يمكنك عرض الاجتماعات القادمة مباشرة من لوحة التحكم الخاصة بك. يتم عرض أحدث 3 اجتماعات قادمة في القسم الجانبي.

You can view upcoming meetings directly from your dashboard. The latest 3 upcoming meetings are displayed in the sidebar section.

## إعداد المهام المجدولة - Setting Up Scheduled Tasks

لضمان إرسال الإشعارات في الوقت المناسب، يجب إعداد مهمة مجدولة لتشغيل أمر إرسال الإشعارات بشكل دوري.

To ensure notifications are sent at the appropriate time, you need to set up a scheduled task to run the notification sending command periodically.

### Windows

1. قم بتشغيل ملف `setup_notification_task.bat` كمسؤول.
2. سيقوم الملف بإنشاء مهمة مجدولة تعمل كل 5 دقائق لإرسال الإشعارات.

1. Run the `setup_notification_task.bat` file as administrator.
2. The file will create a scheduled task that runs every 5 minutes to send notifications.

### يدوياً - Manually

يمكنك أيضاً إعداد المهمة المجدولة يدوياً:

You can also set up the scheduled task manually:

1. افتح "Task Scheduler" من لوحة التحكم.
2. انقر على "Create Basic Task".
3. أدخل اسماً للمهمة، مثل "LMS_Meeting_Notifications".
4. اختر "Daily" أو "When computer starts".
5. اختر "Start a program".
6. اختر ملف `send_notifications.bat`.
7. أكمل المعالج.

1. Open "Task Scheduler" from Control Panel.
2. Click on "Create Basic Task".
3. Enter a name for the task, such as "LMS_Meeting_Notifications".
4. Choose "Daily" or "When computer starts".
5. Choose "Start a program".
6. Browse and select the `send_notifications.bat` file.
7. Complete the wizard.

## استكشاف الأخطاء وإصلاحها - Troubleshooting

### الإشعارات لا تُرسل - Notifications Not Being Sent

1. تأكد من إعداد المهمة المجدولة بشكل صحيح.
2. تحقق من إعدادات البريد الإلكتروني في ملف `settings.py`.
3. تأكد من أن الإشعارات مجدولة للإرسال في المستقبل.
4. تشغيل الأمر يدوياً للتحقق من وجود أخطاء:
   ```
   python manage.py send_meeting_notifications --force
   ```

1. Make sure the scheduled task is set up correctly.
2. Check the email settings in the `settings.py` file.
3. Make sure notifications are scheduled to be sent in the future.
4. Run the command manually to check for errors:
   ```
   python manage.py send_meeting_notifications --force
   ```

### مشاكل في تسجيل الحضور - Attendance Tracking Issues

1. تأكد من أنك مسجل كمشارك في الاجتماع.
2. تأكد من أن الاجتماع نشط وليس ملغياً.
3. تأكد من أن وقت الاجتماع الحالي.

1. Make sure you are registered as a participant in the meeting.
2. Make sure the meeting is active and not cancelled.
3. Make sure the meeting time is current.

## الخلاصة - Conclusion

نظام الاجتماعات هو أداة قوية لإدارة الاجتماعات وتتبع الحضور وإرسال الإشعارات. باتباع هذا الدليل، يمكنك الاستفادة الكاملة من جميع ميزات النظام.

The Meeting System is a powerful tool for managing meetings, tracking attendance, and sending notifications. By following this guide, you can take full advantage of all the system's features.
