from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Category, Tags, Course, Module, Enrollment, CourseReview, ReviewReply,
    UserProgress, ModuleProgress, CourseProgress, Quiz, Question, Answer,
    Attachment, Certification, Exam, ExamQuestion, ExamAnswer, UserExamAttempt,
    UserExamAnswer, Assignment, AssignmentSubmission, Attendance, QuizAttempt,
    QuizUserAnswer, Meeting, Participant, Notification, BookCategory, Review,
    Book, Article, Cart, CartItem, ContentProgress
)
from .models import CertificateTemplate, PresetCertificateTemplate, UserSignature  # Import separately to avoid duplication

# Register your models here
admin.site.register(Category)
admin.site.register(Tags)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Module)
admin.site.register(CourseReview)
admin.site.register(ReviewReply)
admin.site.register(UserProgress)
admin.site.register(ModuleProgress)
admin.site.register(CourseProgress)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Attachment)
admin.site.register(Certification)
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
admin.site.register(Meeting)
admin.site.register(Participant)
admin.site.register(Notification)
admin.site.register(BookCategory)
admin.site.register(Review)
admin.site.register(Book)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ContentProgress)

# Teacher Application Admin
class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'specialization', 'status', 'created_at', 'reviewed_at', 'admin_actions')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('profile__user__username', 'profile__user__email', 'specialization', 'bio')
    readonly_fields = ('created_at', 'reviewed_at', 'admin_actions')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def admin_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}" style="margin-right: 10px;">قبول</a> <a class="button" href="{}" style="color: red;">رفض</a>',
                reverse('approve_teacher_application', args=[obj.id]),
                reverse('reject_teacher_application', args=[obj.id])
            )
        return ""
    admin_actions.short_description = 'إجراءات'
    admin_actions.allow_tags = True
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def approve_selected(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.approve()
        self.message_user(request, f'تم قبول {queryset.count()} طلب بنجاح')
    approve_selected.short_description = 'قبول الطلبات المحددة'
    
    def reject_selected(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.reject(notes='تم الرفض من لوحة الإدارة')
        self.message_user(request, f'تم رفض {queryset.count()} طلب بنجاح')
    reject_selected.short_description = 'رفض الطلبات المحددة'
    
    actions = [approve_selected, reject_selected]

# Enhanced Article admin
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at', 'views_count', 'featured')
    list_filter = ('status', 'featured', 'category', 'created_at')
    search_fields = ('title', 'content', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

admin.site.register(Article, ArticleAdmin)

# Certificate Template Admin
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'created_by', 'template_style', 'template_source', 'primary_color', 'is_public', 'is_default', 'is_active', 'created_at')
    list_filter = ('template_style', 'template_source', 'is_public', 'is_default', 'is_active', 'created_at')
    search_fields = ('template_name', 'institution_name', 'created_by__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('created_by', 'template_name', 'template_style', 'template_source')
        }),
        ('التخصيص', {
            'fields': ('primary_color', 'secondary_color', 'background_pattern', 'border_style', 'font_family')
        }),
        ('معلومات المؤسسة', {
            'fields': ('institution_name', 'institution_logo')
        }),
        ('التوقيع', {
            'fields': ('signature_name', 'signature_title', 'signature_image', 'user_signature')
        }),
        ('نص الشهادة', {
            'fields': ('certificate_text',)
        }),
        ('خيارات الشهادة', {
            'fields': ('include_qr_code', 'include_grade', 'include_completion_date', 'include_course_duration')
        }),
        ('الإعدادات', {
            'fields': ('is_public', 'is_default', 'is_active')
        }),
        ('بيانات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

admin.site.register(CertificateTemplate, CertificateTemplateAdmin)

# Preset Certificate Template Admin
class PresetCertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_style', 'category', 'is_featured', 'is_active', 'created_at')
    list_filter = ('template_style', 'category', 'is_featured', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category')
    date_hierarchy = 'created_at'
    ordering = ('-is_featured', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'category')
        }),
        ('تصميم القالب', {
            'fields': ('template_style', 'primary_color', 'secondary_color', 'background_pattern', 'border_style', 'font_family')
        }),
        ('معاينة القالب', {
            'fields': ('preview_image',)
        }),
        ('كود القالب', {
            'fields': ('template_html', 'template_css'),
            'classes': ('collapse',)
        }),
        ('الإعدادات', {
            'fields': ('is_featured', 'is_active')
        }),
        ('بيانات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

admin.site.register(PresetCertificateTemplate, PresetCertificateTemplateAdmin)

# User Signature Admin
class UserSignatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

admin.site.register(UserSignature, UserSignatureAdmin)

