from user.models import Profile, Teacher
from django.shortcuts import get_object_or_404

def is_teacher(user):
    """
    تحقق مما إذا كان المستخدم معلمًا أو أدمن
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = Profile.objects.get(user=user)
        # Admin has all teacher permissions
        return profile.status == 'Teacher' or profile.status == 'Admin' or user.is_superuser
    except Profile.DoesNotExist:
        return user.is_superuser

def is_course_teacher(user, course):
    """
    تحقق مما إذا كان المستخدم هو معلم الدورة المحددة أو أدمن
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = Profile.objects.get(user=user)
        # Admin has access to all courses
        if profile.status == 'Admin' or user.is_superuser:
            return True
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            return course.teacher == teacher
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        return user.is_superuser
    
    return False

def get_teacher(user):
    """
    الحصول على كائن المعلم للمستخدم إذا كان معلمًا أو أدمن
    """
    if not user.is_authenticated:
        return None
    
    try:
        profile = Profile.objects.get(user=user)
        if profile.status == 'Teacher':
            return Teacher.objects.get(profile=profile)
        elif profile.status == 'Admin' or user.is_superuser:
            # Create a teacher profile for admin if it doesn't exist
            teacher, created = Teacher.objects.get_or_create(
                profile=profile,
                defaults={
                    'bio': 'Administrator with full teacher permissions',
                    'qualification': 'System Administrator'
                }
            )
            return teacher
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        if user.is_superuser:
            # Handle superuser without profile
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'status': 'Admin'
                }
            )
            teacher, created = Teacher.objects.get_or_create(
                profile=profile,
                defaults={
                    'bio': 'Administrator with full teacher permissions',
                    'qualification': 'System Administrator'
                }
            )
            return teacher
    
    return None
