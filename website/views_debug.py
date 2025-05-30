from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from user.models import Teacher
from website.models import Course

@login_required
def debug_teacher_courses(request):
    """
    Debug view to display teacher courses
    """
    # Get teacher info
    teacher_info = {
        'username': request.user.username,
        'profile_status': request.user.profile.status if hasattr(request.user, 'profile') else 'No profile'
    }
    
    # Try to get teacher
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
        teacher_info['teacher_id'] = teacher.id
        teacher_info['teacher_exists'] = True
    except Teacher.DoesNotExist:
        teacher_info['teacher_exists'] = False
        teacher = None
    
    # Get courses if teacher exists
    if teacher:
        courses = Course.objects.filter(teacher=teacher)
        course_info = [{
            'id': course.id,
            'name': course.name,
            'status': course.status,
            'price': course.price
        } for course in courses]
    else:
        course_info = []
    
    context = {
        'teacher_info': teacher_info,
        'course_info': course_info,
        'course_count': len(course_info)
    }
    
    return render(request, 'website/debug_teacher_courses.html', context)
