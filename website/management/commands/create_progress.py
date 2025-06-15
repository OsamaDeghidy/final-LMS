from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from website.models import Course, UserProgress, Enrollment, CourseProgress

class Command(BaseCommand):
    help = 'إنشاء UserProgress للمستخدمين المسجلين في الدورات'

    def handle(self, *args, **options):
        self.stdout.write("🚀 بدء إنشاء سجلات التقدم المفقودة...\n")
        
        try:
            self.create_missing_user_progress()
            self.create_missing_course_progress()
            self.update_all_progress()
            
            self.stdout.write(
                self.style.SUCCESS("\n✅ تم الانتهاء بنجاح!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ خطأ: {e}")
            )

    def create_missing_user_progress(self):
        """إنشاء UserProgress للمستخدمين المسجلين في الدورات"""
        self.stdout.write("إنشاء UserProgress للمستخدمين المسجلين...")
        
        # 1. من خلال Enrollment records
        enrollments = Enrollment.objects.all()
        created_from_enrollments = 0
        
        for enrollment in enrollments:
            user_progress, created = UserProgress.objects.get_or_create(
                user=enrollment.student,
                course=enrollment.course
            )
            if created:
                created_from_enrollments += 1
                self.stdout.write(f"✓ UserProgress created for {enrollment.student.username} in {enrollment.course.name}")
        
        # 2. من خلال ManyToMany relationship في Course
        created_from_m2m = 0
        for course in Course.objects.all():
            for user in course.enroller_user.all():
                user_progress, created = UserProgress.objects.get_or_create(
                    user=user,
                    course=course
                )
                if created:
                    created_from_m2m += 1
                    self.stdout.write(f"✓ UserProgress created for {user.username} in {course.name}")
        
        self.stdout.write(f"\n📊 الإحصائيات:")
        self.stdout.write(f"   - تم إنشاء {created_from_enrollments} سجل من Enrollments")
        self.stdout.write(f"   - تم إنشاء {created_from_m2m} سجل من ManyToMany")
        self.stdout.write(f"   - إجمالي UserProgress: {UserProgress.objects.count()}")

    def create_missing_course_progress(self):
        """إنشاء CourseProgress للدورات"""
        self.stdout.write("\nإنشاء CourseProgress للدورات...")
        
        created_count = 0
        for course in Course.objects.all():
            course_progress, created = CourseProgress.objects.get_or_create(
                course=course
            )
            if created:
                created_count += 1
                self.stdout.write(f"✓ CourseProgress created for {course.name}")
            
            # تحديث الإحصائيات
            course_progress.update_statistics()
        
        self.stdout.write(f"✓ تم إنشاء {created_count} سجل CourseProgress")

    def update_all_progress(self):
        """تحديث جميع سجلات التقدم"""
        self.stdout.write("\nتحديث جميع سجلات التقدم...")
        
        updated_count = 0
        for user_progress in UserProgress.objects.all():
            user_progress.update_progress()
            updated_count += 1
        
        self.stdout.write(f"✓ تم تحديث {updated_count} سجل UserProgress") 