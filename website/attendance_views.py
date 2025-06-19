from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, Sum
from django.contrib import messages
from .models import Course, User, Module, Enrollment, ContentProgress, UserProgress, ModuleProgress
import json
from datetime import datetime
from django.contrib.auth.models import User


@login_required
def attendance_dashboard(request):
    """
    Dashboard view for student progress tracking.
    For students: Shows message that this is for teachers only
    For teachers: Shows student progress statistics for their courses
    """
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    is_admin = hasattr(user, 'profile') and user.profile.status == 'Admin'
    
    if is_teacher or is_admin or user.is_superuser:
        # Get courses taught by this teacher
        courses = Course.objects.filter(teacher__profile__user=user)
        
        # Get progress statistics for each course
        course_stats = []
        for course in courses:
            total_students = course.enroller_user.count()
            total_modules = course.module_set.count()
            
            # Calculate average progress across all students
            enrollments = Enrollment.objects.filter(course=course)
            if enrollments.exists():
                avg_progress = enrollments.aggregate(avg=Avg('progress'))['avg'] or 0
                completed_students = enrollments.filter(progress=100).count()
            else:
                avg_progress = 0
                completed_students = 0
                
            course_stats.append({
                'course': course,
                'total_students': total_students,
                'total_modules': total_modules,
                'avg_progress': avg_progress,
                'completed_students': completed_students,
            })
            
        context = {
            'is_teacher': True,
            'course_stats': course_stats,
        }
    else:
        context = {
            'is_teacher': False,
        }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/dashboard.html', context)


@login_required
def course_attendance(request, course_id):
    """
    View student progress for a specific course
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    is_admin = hasattr(user, 'profile') and user.profile.status == 'Admin'
    
    # Check if user is authorized to view this course's progress
    if (is_teacher or is_admin or user.is_superuser) and course.teacher.profile.user != user and not (is_admin or user.is_superuser):
        messages.error(request, 'ليس لديك صلاحية لعرض تقدم الطلاب في هذه الدورة')
        return redirect('attendance_dashboard')
    
    if not (is_teacher or is_admin or user.is_superuser):
        messages.error(request, 'هذا القسم مخصص للمعلمين فقط')
        return redirect('attendance_dashboard')
    
    # Get all modules for this course
    modules = Module.objects.filter(course=course).order_by('number')
    total_modules = modules.count()
    
    # Get all students enrolled in this course
    students = course.enroller_user.all()
    total_students = students.count()
    
    # Calculate course statistics
    enrollments = Enrollment.objects.filter(course=course)
    avg_progress = enrollments.aggregate(avg=Avg('progress'))['avg'] or 0
    completed_students = enrollments.filter(progress=100).count()
    progress_students = enrollments.filter(progress__gt=0, progress__lt=100).count()
    not_started_students = enrollments.filter(progress=0).count()
    
    # Get detailed progress for each student
    student_progress = []
    for student in students:
        try:
            enrollment = Enrollment.objects.get(student=student, course=course)
            progress_percentage = enrollment.progress or 0
            
            # Count completed content by type
            completed_content = ContentProgress.objects.filter(
                user=student, 
                course=course, 
                completed=True
            )
            
            # Calculate content counts
            total_videos = 0
            total_pdfs = 0
            total_quizzes = 0
            total_assignments = 0
            
            completed_videos = 0
            completed_pdfs = 0
            completed_quizzes = 0
            completed_assignments = 0
            
            # Count total content
            for module in modules:
                if module.video:
                    total_videos += 1
                if module.pdf:
                    total_pdfs += 1
                total_quizzes += module.module_quizzes.filter(is_active=True).count()
                total_assignments += module.module_assignments.filter(is_active=True).count()
            
            # Add course-level content
            total_quizzes += course.course_quizzes.filter(is_active=True).count()
            total_assignments += course.assignments.filter(is_active=True).count()
            
            # Count completed content
            for content in completed_content:
                if content.content_type == 'video':
                    completed_videos += 1
                elif content.content_type in ['pdf', 'note']:
                    completed_pdfs += 1
                elif content.content_type == 'quiz':
                    completed_quizzes += 1
                elif content.content_type == 'assignment':
                    completed_assignments += 1
            
            student_progress.append({
                'student': student,
                'progress_percentage': progress_percentage,
                'enrollment_date': enrollment.enrollment_date,
                'last_activity': enrollment.last_accessed,
                'completion_date': None,  # You can add this field to Enrollment model if needed
                'total_videos': total_videos,
                'completed_videos': completed_videos,
                'total_pdfs': total_pdfs,
                'completed_pdfs': completed_pdfs,
                'total_quizzes': total_quizzes,
                'completed_quizzes': completed_quizzes,
                'total_assignments': total_assignments,
                'completed_assignments': completed_assignments,
            })
            
        except Enrollment.DoesNotExist:
            continue
    
    context = {
        'course': course,
        'modules': modules,
        'is_teacher': True,
        'student_progress': student_progress,
        'total_students': total_students,
        'total_modules': total_modules,
        'avg_progress': avg_progress,
        'completed_students': completed_students,
        'progress_students': progress_students,
        'not_started_students': not_started_students,
    }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/course_attendance.html', context)


# All old attendance functions have been removed and replaced with student progress tracking system
