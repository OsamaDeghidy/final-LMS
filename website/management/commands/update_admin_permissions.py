from django.core.management.base import BaseCommand
from user.models import Profile, Teacher
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Update admin permissions to include all teacher permissions'

    def handle(self, *args, **options):
        self.stdout.write("بدء تحديث صلاحيات الأدمن...")
        
        # البحث عن جميع المستخدمين الذين لديهم صلاحيات أدمن
        admin_profiles = Profile.objects.filter(status='Admin')
        superusers = User.objects.filter(is_superuser=True)
        
        updated_count = 0
        
        # تحديث صلاحيات الأدمن العاديين
        for profile in admin_profiles:
            self.stdout.write(f"تحديث صلاحيات الأدمن: {profile.name} ({profile.user.username})")
            
            # إنشاء كائن معلم للأدمن إذا لم يكن موجوداً
            teacher, created = Teacher.objects.get_or_create(
                profile=profile,
                defaults={
                    'bio': 'Administrator with full teacher permissions',
                    'qualification': 'System Administrator',
                    'department': 'Administration'
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ تم إنشاء كائن معلم جديد للأدمن: {profile.name}")
            else:
                self.stdout.write(f"  ✓ كائن المعلم موجود بالفعل للأدمن: {profile.name}")
            
            updated_count += 1
        
        # تحديث صلاحيات المستخدمين الفائقين
        for user in superusers:
            self.stdout.write(f"تحديث صلاحيات المستخدم الفائق: {user.username}")
            
            # إنشاء أو تحديث profile للمستخدم الفائق
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'status': 'Admin'
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ تم إنشاء profile جديد للمستخدم الفائق: {user.username}")
            elif profile.status != 'Admin':
                profile.status = 'Admin'
                profile.save()
                self.stdout.write(f"  ✓ تم تحديث status المستخدم الفائق إلى Admin: {user.username}")
            
            # إنشاء كائن معلم للمستخدم الفائق
            teacher, created = Teacher.objects.get_or_create(
                profile=profile,
                defaults={
                    'bio': 'System Administrator with full teacher permissions',
                    'qualification': 'System Administrator',
                    'department': 'System Administration'
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ تم إنشاء كائن معلم جديد للمستخدم الفائق: {user.username}")
            else:
                self.stdout.write(f"  ✓ كائن المعلم موجود بالفعل للمستخدم الفائق: {user.username}")
            
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ تم تحديث صلاحيات {updated_count} مستخدم أدمن بنجاح!")
        )
        self.stdout.write("الآن جميع المستخدمين الأدمن لديهم نفس صلاحيات المعلمين.") 