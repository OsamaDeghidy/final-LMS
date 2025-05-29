from user.models import Profile, Teacher
from django.shortcuts import get_object_or_404

def is_teacher(user):
    """
    تحقق مما إذا كان المستخدم معلمًا
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = Profile.objects.get(user=user)
        return profile.status == 'Teacher'
    except Profile.DoesNotExist:
        return False

def is_course_teacher(user, course):
    """
    تحقق مما إذا كان المستخدم هو معلم الدورة المحددة
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = Profile.objects.get(user=user)
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            return course.teacher == teacher
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        return False
    
    return False

def get_teacher(user):
    """
    الحصول على كائن المعلم للمستخدم إذا كان معلمًا
    """
    if not user.is_authenticated:
        return None
    
    try:
        profile = Profile.objects.get(user=user)
        if profile.status == 'Teacher':
            return Teacher.objects.get(profile=profile)
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        return None
    
    return None
