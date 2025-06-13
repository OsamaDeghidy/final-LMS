from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from user.models import Profile
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix duplicate profiles and clean database'

    def handle(self, *args, **options):
        self.stdout.write("بدء فحص وإصلاح Profiles المكررة...")
        
        fixed_count = 0
        
        # البحص عن المستخدمين بدون profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        self.stdout.write(f"وجد {users_without_profiles.count()} مستخدم بدون profile")
        
        for user in users_without_profiles:
            with transaction.atomic():
                # إنشاء profile للمستخدمين الذين لا يملكون profiles
                status = 'Admin' if user.is_superuser else 'Student'
                Profile.objects.create(
                    user=user,
                    name=user.get_full_name() or user.username,
                    email=user.email,
                    status=status
                )
                self.stdout.write(f"  ✓ تم إنشاء profile للمستخدم: {user.username}")
                fixed_count += 1
        
        # البحث عن profiles مكررة (نفس المستخدم)
        from django.db.models import Count
        duplicate_users = Profile.objects.values('user').annotate(
            count=Count('user')
        ).filter(count__gt=1)
        
        for duplicate in duplicate_users:
            user_id = duplicate['user']
            profiles = Profile.objects.filter(user_id=user_id).order_by('id')
            self.stdout.write(f"وجد {profiles.count()} profiles للمستخدم {user_id}")
            
            # الاحتفاظ بأول profile وحذف الباقي
            first_profile = profiles.first()
            duplicate_profiles = profiles[1:]
            
            for profile in duplicate_profiles:
                self.stdout.write(f"  ✗ حذف profile مكرر: {profile.id}")
                profile.delete()
                fixed_count += 1
        
        # البحث عن profiles بدون مستخدمين
        orphan_profiles = Profile.objects.filter(user__isnull=True)
        self.stdout.write(f"وجد {orphan_profiles.count()} profile بدون مستخدم")
        
        for profile in orphan_profiles:
            self.stdout.write(f"  ✗ حذف profile يتيم: {profile.id}")
            profile.delete()
            fixed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ تم إصلاح {fixed_count} مشكلة في قاعدة البيانات!")
        )
        self.stdout.write("قاعدة البيانات نظيفة الآن.") 