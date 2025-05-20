from django.contrib import admin
from .models import Category, Tags, Course, Module, Video, Comment, SubComment, Notes, Monitor, UserProgress, CourseProgress, Quiz, Question, Answer, Enrollment, Certification, Attachment, Exam, ExamQuestion, ExamAnswer, UserExamAttempt, UserExamAnswer, Assignment, AssignmentSubmission, Attendance, QuizAttempt, QuizUserAnswer

# Register your models here.

admin.site.register(Category)
admin.site.register(Tags)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Video)
admin.site.register(Comment)
admin.site.register(SubComment)
admin.site.register(Notes)
admin.site.register(Monitor)
admin.site.register(UserProgress)
admin.site.register(CourseProgress)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Enrollment)
admin.site.register(Certification)
admin.site.register(Attachment)
admin.site.register(Exam)
admin.site.register(ExamQuestion)
admin.site.register(ExamAnswer)
admin.site.register(UserExamAttempt)
admin.site.register(UserExamAnswer)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Attendance)
admin.site.register(QuizAttempt)
admin.site.register(QuizUserAnswer)


