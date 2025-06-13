from django.core.management.base import BaseCommand
from django.db import transaction
from user.models import TeacherApplication, Teacher, Profile
import logging


class Command(BaseCommand):
    help = 'إصلاح طلبات المعلمين المعتمدة التي تفتقر لكائنات المعلمين'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض ما سيتم إصلاحه دون تطبيق التغييرات',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🔍 البحث عن طلبات المعلمين المعتمدة بدون كائنات معلمين...'))
        
        # البحث عن الطلبات المعتمدة
        approved_applications = TeacherApplication.objects.filter(status='approved')
        
        problems_found = []
        
        for app in approved_applications:
            try:
                profile = app.profile
                
                # التحقق من وجود كائن المعلم
                if not hasattr(profile, 'teacher') or not Teacher.objects.filter(profile=profile).exists():
                    problems_found.append({
                        'application': app,
                        'profile': profile,
                        'email': profile.user.email,
                        'issue': 'missing_teacher_object'
                    })
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  الطلب المعتمد {profile.user.email} يفتقر لكائن المعلم')
                    )
                
                # التحقق من حالة الملف الشخصي
                if profile.status != 'Teacher':
                    problems_found.append({
                        'application': app,
                        'profile': profile,
                        'email': profile.user.email,
                        'issue': 'wrong_status',
                        'current_status': profile.status
                    })
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  الطلب المعتمد {profile.user.email} حالة الملف الشخصي: {profile.status}')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ خطأ في معالجة الطلب: {str(e)}')
                )
        
        if not problems_found:
            self.stdout.write(self.style.SUCCESS('✅ جميع طلبات المعلمين المعتمدة تعمل بشكل صحيح!'))
            return
        
        self.stdout.write(f'\n🔧 تم العثور على {len(problems_found)} مشكلة.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 وضع المعاينة - لن يتم تطبيق أي تغييرات'))
            for problem in problems_found:
                self.stdout.write(f'   - {problem["email"]}: {problem["issue"]}')
            return
        
        # إصلاح المشاكل
        fixed_count = 0
        
        for problem in problems_found:
            try:
                with transaction.atomic():
                    app = problem['application']
                    profile = problem['profile']
                    
                    self.stdout.write(f'🔧 إصلاح {profile.user.email}...')
                    
                    # تحديث حالة الملف الشخصي
                    if profile.status != 'Teacher':
                        profile.status = 'Teacher'
                        profile.save(update_fields=['status'])
                        self.stdout.write(f'   ✅ تم تحديث حالة الملف الشخصي إلى Teacher')
                    
                    # إنشاء كائن المعلم إذا لم يكن موجوداً
                    if not Teacher.objects.filter(profile=profile).exists():
                        teacher = Teacher.objects.create(
                            profile=profile,
                            bio=getattr(app, 'bio', 'معلم معتمد'),
                            qualification=getattr(app, 'specialization', 'غير محدد')
                        )
                        self.stdout.write(f'   ✅ تم إنشاء كائن المعلم (ID: {teacher.id})')
                    
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ تم إصلاح {profile.user.email} بنجاح')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ فشل في إصلاح {profile.user.email}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 تم إصلاح {fixed_count} من أصل {len(problems_found)} مشكلة!')
        )
        
        # فحص نهائي
        self.stdout.write('\n🔍 فحص نهائي...')
        remaining_issues = 0
        
        for app in TeacherApplication.objects.filter(status='approved'):
            profile = app.profile
            if profile.status != 'Teacher':
                remaining_issues += 1
                self.stdout.write(f'⚠️  {profile.user.email}: حالة خاطئة ({profile.status})')
            elif not Teacher.objects.filter(profile=profile).exists():
                remaining_issues += 1
                self.stdout.write(f'⚠️  {profile.user.email}: كائن المعلم مفقود')
        
        if remaining_issues == 0:
            self.stdout.write(self.style.SUCCESS('✅ جميع المشاكل تم حلها!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  يوجد {remaining_issues} مشكلة متبقية')) 