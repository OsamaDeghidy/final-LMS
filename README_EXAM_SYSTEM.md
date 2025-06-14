# نظام الاختبارات - Exam System Documentation

## نظرة عامة - Overview
نظام الاختبارات هو جزء متكامل من منصة التعلم الإلكتروني، يتيح للمعلمين إنشاء وإدارة الاختبارات المختلفة، ويمكن الطلاب من أداء هذه الاختبارات وعرض نتائجهم.

The Exam System is an integrated part of the LMS platform, allowing teachers to create and manage various exams, and enabling students to take these exams and view their results.

## الميزات الرئيسية - Key Features

### للمعلمين - For Teachers
- إنشاء اختبارات متنوعة مع خيارات متعددة للتخصيص
- إضافة أسئلة متعددة الخيارات، صح/خطأ، وأسئلة الإجابة القصيرة
- تحديد وقت الاختبار، درجة النجاح، وعدد المحاولات المسموحة
- إمكانية ترتيب الأسئلة وتحديد نقاط لكل سؤال
- عرض محاولات الطلاب وتصحيح الأسئلة ذات الإجابات القصيرة
- إمكانية تحديد موعد بدء وانتهاء الاختبار

### للطلاب - For Students
- عرض الاختبارات المتاحة ضمن الدورة التدريبية
- أداء الاختبارات مع عداد للوقت المتبقي
- حفظ الإجابات تلقائياً أثناء الاختبار
- عرض نتائج الاختبار مباشرة بعد الانتهاء
- إمكانية إعادة المحاولة حسب إعدادات الاختبار

## المكونات الرئيسية - Main Components

### النماذج - Models
- `Exam`: نموذج الاختبار الرئيسي مع جميع الإعدادات والخصائص
- `ExamQuestion`: نموذج الأسئلة بأنواعها المختلفة
- `ExamAnswer`: نموذج الإجابات المحتملة للأسئلة
- `ExamAttempt`: نموذج محاولات الطلاب لأداء الاختبار
- `ExamResponse`: نموذج إجابات الطلاب على الأسئلة

### صفحات المعلم - Teacher Pages
- `teacher_exams.html`: عرض قائمة الاختبارات للدورة
- `create_exam.html`: إنشاء اختبار جديد
- `edit_exam.html`: تعديل اختبار موجود
- `delete_exam.html`: حذف اختبار مع تأكيد
- `add_question.html`: إضافة سؤال جديد
- `edit_question.html`: تعديل سؤال موجود
- `delete_question.html`: حذف سؤال مع تأكيد
- `teacher_exam_attempts.html`: عرض محاولات الطلاب
- `grade_short_answers.html`: تصحيح أسئلة الإجابة القصيرة

### صفحات الطالب - Student Pages
- `student_exams.html`: عرض الاختبارات المتاحة للطالب
- `take_exam.html`: صفحة أداء الاختبار
- `exam_results.html`: عرض نتائج الاختبار

## كيفية الاستخدام - How to Use

### إنشاء اختبار جديد - Create a New Exam
1. انتقل إلى صفحة الدورة التدريبية
2. انقر على تبويب "الاختبارات"
3. انقر على زر "إنشاء اختبار جديد"
4. املأ النموذج بالمعلومات المطلوبة وحدد الخيارات المناسبة
5. انقر على "إنشاء الاختبار"

### إضافة أسئلة - Add Questions
1. بعد إنشاء الاختبار، انقر على "إضافة سؤال"
2. اختر نوع السؤال (متعدد الخيارات، صح/خطأ، إجابة قصيرة)
3. أدخل نص السؤال والإجابات المحتملة
4. حدد الإجابة الصحيحة ونقاط السؤال
5. انقر على "حفظ السؤال"

### أداء اختبار - Take an Exam
1. انتقل إلى صفحة الدورة التدريبية
2. انقر على تبويب "الاختبارات"
3. اختر الاختبار المطلوب وانقر على "بدء الاختبار"
4. أجب على الأسئلة ضمن الوقت المحدد
5. انقر على "إنهاء وتسليم الاختبار" عند الانتهاء

## المتطلبات التقنية - Technical Requirements
- Django 3.2+
- JavaScript (ES6+)
- Bootstrap 5
- Font Awesome 5
- Sortable.js (لترتيب الأسئلة)

## ملاحظات تقنية - Technical Notes
- يتم حفظ إجابات الطلاب تلقائياً كل 30 ثانية
- يتم استخدام AJAX لترتيب الأسئلة وحفظ الإجابات
- يتم التحقق من صلاحيات المستخدم لكل عملية
- يتم استخدام نظام التوقيت للاختبارات المحددة بوقت
- يتم استخدام نظام التنقيط التلقائي للأسئلة متعددة الخيارات وأسئلة صح/خطأ
- يتم استخدام نظام التصحيح اليدوي للأسئلة ذات الإجابات القصيرة

## الملفات الرئيسية - Key Files
- `website/exam_views.py`: وجهات نظر الاختبارات
- `website/urls_exam.py`: عناوين URL للاختبارات
- `website/models.py`: نماذج قاعدة البيانات
- `static/js/exam.js`: وظائف JavaScript للاختبارات
- `static/js/exam_questions.js`: وظائف JavaScript لإدارة الأسئلة
- `templates/website/exams/`: قوالب HTML للاختبارات

## التكامل مع نظام LMS - Integration with LMS
تم دمج نظام الاختبارات بشكل كامل مع نظام إدارة التعلم الرئيسي، حيث يمكن الوصول إليه من خلال صفحة تفاصيل الدورة التدريبية. يتم احتساب نتائج الاختبارات ضمن تقدم الطالب في الدورة، ويمكن للمعلمين متابعة أداء الطلاب من خلال لوحة التحكم.

The Exam System is fully integrated with the main Learning Management System, accessible through the course detail page. Exam results are counted towards student progress in the course, and teachers can monitor student performance through the dashboard.
