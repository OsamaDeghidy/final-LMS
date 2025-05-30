from django.contrib import admin
from .models import Category, Tags, Course, Module, Video, Comment, SubComment, Notes, Monitor, UserProgress, CourseProgress, Quiz, Question, Answer, Enrollment, Certification, Attachment, Exam, ExamQuestion, ExamAnswer, UserExamAttempt, UserExamAnswer, Assignment, AssignmentSubmission, Attendance, QuizAttempt, QuizUserAnswer, School, Meeting, Participant, Notification, BookCategory, Book, Article

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

# Register new models
admin.site.register(School)
admin.site.register(Meeting)
admin.site.register(Participant)
admin.site.register(Notification)
admin.site.register(BookCategory)
admin.site.register(Book)

# Enhanced Article admin
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at', 'views_count', 'featured')
    list_filter = ('status', 'featured', 'category', 'created_at')
    search_fields = ('title', 'content', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

admin.site.register(Article, ArticleAdmin)

