from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseForbidden

from .models import Course, Enrollment, VideoProgress, Module, Video
from user.models import Profile, Student, Teacher

@login_required
def my_courses(request):
    """
    Display all courses the student is enrolled in
    """
    # Get user profile data for dashboard template
    profile = Profile.objects.get(user=request.user)
    
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
        'course__module_set',
        'course__module_set__video_set'
    )
    
    # Calculate progress for each enrollment
    for enrollment in enrollments:
        # Calculate total videos in course
        total_videos = sum(module.video_set.count() for module in enrollment.course.module_set.all())
        
        if total_videos > 0:
            # Get watched videos for this course
            watched_videos = VideoProgress.objects.filter(
                student=request.user,
                video__module__course=enrollment.course,
                watched=True
            ).count()
            
            # Calculate progress percentage
            progress = (watched_videos / total_videos) * 100
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
    profile = Profile.objects.get(user=request.user)
    
    # Check if user is a teacher
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        # User is not a teacher, redirect to student courses
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('my_courses')
    
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
        'module_set__video_set',
        'enrollments'
    )
    
    # Calculate stats for each course
    for course in courses:
        # Count total modules
        course.total_modules = course.module_set.count()
        
        # Count total videos
        course.total_videos = Video.objects.filter(module__course=course).count()
        
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
