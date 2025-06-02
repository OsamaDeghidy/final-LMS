from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Profile, Organization, Teacher, Student, TeacherApplication
from django.utils import timezone

class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'specialization', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('profile__user__username', 'specialization', 'bio')
    readonly_fields = ('created_at', 'reviewed_at')
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        from django.db import transaction
        
        for application in queryset:
            if application.status == 'pending':
                try:
                    with transaction.atomic():
                        # First, update the profile status directly
                        profile = application.profile
                        profile.status = 'Teacher'
                        profile.save(update_fields=['status'])
                        
                        # Create or update the teacher profile
                        teacher, created = Teacher.objects.get_or_create(
                            profile=profile,
                            defaults={
                                'bio': application.bio,
                                'qualification': application.specialization
                            }
                        )
                        
                        if not created:
                            teacher.bio = application.bio
                            teacher.qualification = application.specialization
                            teacher.save(update_fields=['bio', 'qualification'])
                        
                        # Delete student profile if it exists
                        Student.objects.filter(profile=profile).delete()
                        
                        # Update the application status
                        application.status = 'approved'
                        application.reviewed_at = timezone.now()
                        application.save(update_fields=['status', 'reviewed_at'])
                        
                        self.message_user(request, f'تم قبول طلب {application.profile.user.username} بنجاح')
                        
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error approving application {application.id}: {str(e)}", exc_info=True)
                    self.message_user(
                        request, 
                        f'فشل في قبول طلب {application.profile.user.username}: {str(e)}', 
                        level='ERROR'
                    )
    approve_applications.short_description = 'قبول الطلبات المحددة'
    
    def reject_applications(self, request, queryset):
        for application in queryset:
            if application.status == 'pending':
                if application.reject('تم الرفض من قبل المشرف'):
                    self.message_user(request, f'تم رفض طلب {application.profile.user.username} بنجاح')
                else:
                    self.message_user(request, f'فشل في رفض طلب {application.profile.user.username}', level='ERROR')
    reject_applications.short_description = 'رفض الطلبات المحددة'

# Register your models here.
admin.site.register(Profile)
admin.site.register(Organization)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(TeacherApplication, TeacherApplicationAdmin)