from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseForbidden

from .models import Course, Enrollment, Module, UserProgress, ModuleProgress
from user.models import Profile, Student, Teacher

@login_required
def my_courses(request):
    """
    Display all courses the student is enrolled in
    """
    # Get user profile data for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم. يرجى التواصل مع مسؤول النظام.')
        return redirect('home')
    
    # Get student or teacher data if available
    student = None
    teacher = None
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        pass
    
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        pass
    
    # Get all enrollments for the user
    enrollments = Enrollment.objects.filter(student=request.user).select_related(
        'course',
        'course__teacher__profile'
    ).prefetch_related(
        'course__tags',
        'course__module_set'
    )
    
    # Calculate progress for each enrollment
    for enrollment in enrollments:
        # Calculate total modules with videos in course
        total_modules = enrollment.course.module_set.filter(video__isnull=False).count()
        
        if total_modules > 0:
            # Get completed modules for this course using ModuleProgress
            completed_modules = ModuleProgress.objects.filter(
                user=request.user,
                module__course=enrollment.course,
                video_watched=True
            ).count()
            
            # Calculate progress percentage
            progress = (completed_modules / total_modules) * 100
        else:
            progress = 0
            
        # Update enrollment progress
        enrollment.progress = progress
        enrollment.save(update_fields=['progress'])
        
        # Set completed flag
        enrollment.completed = progress == 100
    
    context = {
        'profile': profile,
        'student': student,
        'teacher': teacher,
        'enrollments': enrollments,
    }
    
    return render(request, 'website/my_courses.html', context)

@login_required
def teacher_courses(request):
    """
    Display all courses created by the teacher
    """
    # Get user profile data for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم. يرجى التواصل مع مسؤول النظام.')
        return redirect('home')
    
    # Check if user is a teacher or admin
    if profile.status not in ['Teacher', 'Admin']:
        # User is not a teacher or admin, redirect to dashboard
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
        
    # Get teacher record
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        # Create teacher record if it doesn't exist but user has Teacher status
        teacher = Teacher.objects.create(profile=profile)
    
    # Get student data if available (for the template)
    student = None
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        pass
    
    # Get all courses created by this teacher
    courses = Course.objects.filter(teacher=teacher).prefetch_related(
        'tags',
        'module_set',
        'enrollments'
    )
    
    # Calculate stats for each course
    for course in courses:
        # Count total modules
        course.total_modules = course.module_set.count()
        
        # Count total modules with videos
        course.total_videos = course.module_set.filter(video__isnull=False).count()
        
        # Count total students enrolled
        course.total_students = course.enrollments.count()
        
        # Calculate average progress
        if course.total_students > 0:
            total_progress = sum(enrollment.progress for enrollment in course.enrollments.all())
            course.avg_progress = total_progress / course.total_students
        else:
            course.avg_progress = 0
    
    context = {
        'profile': profile,
        'student': student,
        'teacher': teacher,
        'courses': courses,
    }
    
    return render(request, 'website/teacher_courses.html', context)
