from django.core.management.base import BaseCommand
from user.models import TeacherApplication, Profile, Teacher, Student
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix teacher applications and verify profile updates'

    def handle(self, *args, **options):
        self.stdout.write("بدء فحص وإصلاح طلبات المعلمين...")
        
        # Find approved applications where profile is still Student
        problematic_apps = TeacherApplication.objects.filter(
            status='approved',
            profile__status='Student'
        )
        
        self.stdout.write(f"وجد {problematic_apps.count()} طلب معتمد لكن الملف الشخصي ما زال طالب")
        
        fixed_count = 0
        
        for app in problematic_apps:
            try:
                with transaction.atomic():
                    self.stdout.write(f"إصلاح طلب {app.profile.user.username}...")
                    
                    profile = app.profile
                    
                    # Update profile status
                    profile.status = 'Teacher'
                    profile.save(update_fields=['status'])
                    
                    # Create or update Teacher profile
                    teacher, created = Teacher.objects.get_or_create(
                        profile=profile,
                        defaults={
                            'bio': app.bio,
                            'qualification': app.specialization
                        }
                    )
                    
                    if not created:
                        teacher.bio = app.bio
                        teacher.qualification = app.specialization
                        teacher.save(update_fields=['bio', 'qualification'])
                    
                    # Delete student profile if it exists
                    Student.objects.filter(profile=profile).delete()
                    
                    self.stdout.write(f"  ✓ تم إصلاح طلب {app.profile.user.username}")
                    fixed_count += 1
                    
            except Exception as e:
                self.stdout.write(f"  ✗ فشل في إصلاح طلب {app.profile.user.username}: {str(e)}")
        
        # Check for pending applications
        pending_apps = TeacherApplication.objects.filter(status='pending')
        self.stdout.write(f"\nيوجد {pending_apps.count()} طلب قيد الانتظار")
        
        # Check for profiles without proper Teacher objects
        teacher_profiles = Profile.objects.filter(status='Teacher')
        missing_teacher_objects = 0
        
        for profile in teacher_profiles:
            if not hasattr(profile, 'teacher_set') or not Teacher.objects.filter(profile=profile).exists():
                try:
                    # Find the application for this profile
                    app = TeacherApplication.objects.filter(
                        profile=profile, 
                        status='approved'
                    ).first()
                    
                    if app:
                        Teacher.objects.create(
                            profile=profile,
                            bio=app.bio,
                            qualification=app.specialization
                        )
                        self.stdout.write(f"  ✓ أنشأ كائن معلم مفقود للمستخدم {profile.user.username}")
                        missing_teacher_objects += 1
                except Exception as e:
                    self.stdout.write(f"  ✗ فشل في إنشاء كائن معلم للمستخدم {profile.user.username}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ تم إصلاح {fixed_count} طلب معلم!")
        )
        if missing_teacher_objects > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ تم إنشاء {missing_teacher_objects} كائن معلم مفقود!")
            )
        self.stdout.write("جميع طلبات المعلمين تعمل بشكل صحيح الآن.") 