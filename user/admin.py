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
        approved_count = 0
        failed_count = 0
        
        for application in queryset.filter(status='pending'):
            try:
                success = application.approve()
                if success:
                    approved_count += 1
                    self.message_user(request, f'✅ تم قبول طلب {application.profile.user.username} بنجاح')
                else:
                    failed_count += 1
                    self.message_user(
                        request, 
                        f'❌ فشل في قبول طلب {application.profile.user.username}', 
                        level='ERROR'
                    )
            except Exception as e:
                failed_count += 1
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error approving application {application.id}: {str(e)}", exc_info=True)
                self.message_user(
                    request, 
                    f'❌ فشل في قبول طلب {application.profile.user.username}: {str(e)}', 
                    level='ERROR'
                )
        
        # Summary message
        if approved_count > 0:
            self.message_user(request, f'تم قبول {approved_count} طلب بنجاح')
        if failed_count > 0:
            self.message_user(request, f'فشل في قبول {failed_count} طلب', level='ERROR')
            
    approve_applications.short_description = 'قبول الطلبات المحددة'
    
    def reject_applications(self, request, queryset):
        rejected_count = 0
        failed_count = 0
        
        for application in queryset.filter(status='pending'):
            try:
                success = application.reject('تم الرفض من قبل المشرف')
                if success:
                    rejected_count += 1
                    self.message_user(request, f'✅ تم رفض طلب {application.profile.user.username} بنجاح')
                else:
                    failed_count += 1
                    self.message_user(
                        request, 
                        f'❌ فشل في رفض طلب {application.profile.user.username}', 
                        level='ERROR'
                    )
            except Exception as e:
                failed_count += 1
                self.message_user(
                    request, 
                    f'❌ فشل في رفض طلب {application.profile.user.username}: {str(e)}', 
                    level='ERROR'
                )
        
        # Summary message
        if rejected_count > 0:
            self.message_user(request, f'تم رفض {rejected_count} طلب بنجاح')
        if failed_count > 0:
            self.message_user(request, f'فشل في رفض {failed_count} طلب', level='ERROR')
            
    reject_applications.short_description = 'رفض الطلبات المحددة'

# Register your models here.
admin.site.register(Profile)
admin.site.register(Organization)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(TeacherApplication, TeacherApplicationAdmin)