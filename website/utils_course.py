from django.db.models import Q, Count, Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
from .models import (
    Course, Module, Tags, Quiz, Question, Answer, Enrollment, 
    Assignment, AssignmentSubmission, UserExamAttempt, ContentProgress,
    UserProgress, ModuleProgress, CourseProgress, ContentType
)
from user.models import Profile, Student, Organization, Teacher


def searchCourses(request):
    """
    Search for courses based on query parameters
    """
    search_query = ''

    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')

    courses = Course.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(small_description__icontains=search_query) |
        Q(learned__icontains=search_query) |
        Q(tags__name__icontains=search_query) |
        Q(module__name__icontains=search_query) |
        Q(module__description__icontains=search_query)
    )

    return courses, search_query


def update_enrollment_progress(enrollment):
    """
    Updates the progress of a student's enrollment in a course
    Enhanced to work with new module-based content system
    """
    try:
        course = enrollment.course
        student = enrollment.student
        
        print(f"[DEBUG] Updating progress for {student.username} in course {course.name}")
        
        # Count total content items in the course
        total_content = 0
        
        # Count module-based content
        modules = course.module_set.all()
        for module in modules:
            # Count videos
            if module.video:
                total_content += 1
            # Count PDFs
            if module.pdf:
                total_content += 1
            # Count notes
            if module.note:
                total_content += 1
            # Count module quizzes
            total_content += module.module_quizzes.filter(is_active=True).count()
            # Count module assignments
            total_content += module.module_assignments.filter(is_active=True).count()
        
        # Add course-level quizzes and assignments
        total_content += course.course_quizzes.filter(is_active=True).count()
        total_content += course.assignments.filter(is_active=True).count()
        
        print(f"[DEBUG] Total content items: {total_content}")
        
        if total_content == 0:
            enrollment.progress = 0.0
            enrollment.save(update_fields=['progress'])
            return 0.0
        
        # Count completed items
        completed_count = ContentProgress.objects.filter(
            user=student,
            course=course,
            completed=True
        ).count()
        
        print(f"[DEBUG] Completed items: {completed_count}")
        
        # Calculate progress percentage
        progress = (completed_count / total_content * 100) if total_content > 0 else 0
        progress = round(progress, 2)
        
        # Update enrollment
        enrollment.progress = progress
        enrollment.last_accessed = timezone.now()
        
        # Update status based on progress
        if progress >= 95:
            enrollment.status = 'completed'
        elif progress > 0:
            enrollment.status = 'active'
        else:
            enrollment.status = 'active'
        
        enrollment.save(update_fields=['progress', 'last_accessed', 'status'])
        print(f"[DEBUG] Final progress saved: {enrollment.progress}%")
        
        return enrollment.progress
        
    except Exception as e:
        print(f"[ERROR] Error in update_enrollment_progress: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def mark_content_completed(user, course, content_type, content_id):
    """
    Mark a specific content item as completed
    Enhanced to support all content types including module-based content
    """
    try:
        # Ensure content_id is a string for storage
        content_id_str = str(content_id)
        
        # Create or update content progress
        progress_item, created = ContentProgress.objects.get_or_create(
            user=user,
            course=course,
            content_type=content_type,
            content_id=content_id_str,
            defaults={
                'completed': True,
                'completion_date': timezone.now(),
                'last_accessed': timezone.now()
            }
        )
        
        if not created and not progress_item.completed:
            progress_item.completed = True
            progress_item.completion_date = timezone.now()
            progress_item.last_accessed = timezone.now()
            progress_item.save(update_fields=['completed', 'completion_date', 'last_accessed'])
        
        print(f"[DEBUG] Marked {content_type} {content_id} as completed for {user.username}")
        
        # Update enrollment progress
        try:
            enrollment = Enrollment.objects.get(student=user, course=course)
            return update_enrollment_progress(enrollment)
        except Enrollment.DoesNotExist:
            print(f"[WARNING] No enrollment found for {user.username} in course {course.name}")
            return 0
            
    except Exception as e:
        print(f"[ERROR] Error marking content completed: {e}")
        import traceback
        traceback.print_exc()
        return 0


def get_completed_content_ids(user, course, content_type):
    """
    Get list of completed content IDs for a specific type
    Enhanced to support module-based content tracking
    """
    completed_items = []
    
    if content_type == 'video':
        # Get completed module videos
        video_progress = ContentProgress.objects.filter(
            user=user,
            course=course,
            content_type='video',
            completed=True
        ).values_list('content_id', flat=True)
        
        # Convert module_video_X format to content IDs
        for item in video_progress:
            if item.startswith('module_video_'):
                module_id = item.replace('module_video_', '')
                if module_id.isdigit():
                    completed_items.append(item)
    
    elif content_type == 'pdf':
        # Get completed module PDFs
        pdf_progress = ContentProgress.objects.filter(
            user=user,
            course=course,
            content_type='pdf',
            completed=True
        ).values_list('content_id', flat=True)
        
        for item in pdf_progress:
            if item.startswith('module_pdf_'):
                module_id = item.replace('module_pdf_', '')
                if module_id.isdigit():
                    completed_items.append(item)
    
    elif content_type == 'note':
        # Get completed module notes
        note_progress = ContentProgress.objects.filter(
            user=user,
            course=course,
            content_type='note',
            completed=True
        ).values_list('content_id', flat=True)
        
        for item in note_progress:
            if item.startswith('module_note_'):
                module_id = item.replace('module_note_', '')
                if module_id.isdigit():
                    completed_items.append(item)
    
    elif content_type == 'quiz':
        # Get completed quizzes (both module and course level)
        quiz_progress = ContentProgress.objects.filter(
            user=user,
            course=course,
            content_type='quiz',
            completed=True
        ).values_list('content_id', flat=True)
        
        # Convert to integers
        completed_items = [int(item) for item in quiz_progress if item.isdigit()]
    
    elif content_type == 'assignment':
        # Get completed assignments (both module and course level)
        assignment_progress = ContentProgress.objects.filter(
            user=user,
            course=course,
            content_type='assignment',
            completed=True
        ).values_list('content_id', flat=True)
        
        # Convert to integers
        completed_items = [int(item) for item in assignment_progress if item.isdigit()]
    
    return completed_items


def get_user_course_progress(user, course):
    """
    Gets the progress for a specific user in a specific course
    """
    try:
        enrollment = Enrollment.objects.get(student=user, course=course)
        return enrollment.progress
    except Enrollment.DoesNotExist:
        return 0


def get_user_enrolled_courses(user):
    """
    Gets all courses a user is enrolled in with their progress
    """
    enrollments = Enrollment.objects.filter(student=user, status='active')
    enrolled_courses = []
    
    for enrollment in enrollments:
        enrolled_courses.append({
            'course': enrollment.course,
            'progress': enrollment.progress,
            'enrollment_date': enrollment.enrollment_date,
            'last_accessed': enrollment.last_accessed
        })
    
    return enrolled_courses


def ensure_course_has_module(course):
    """
    Ensure that a course has at least one module. Create one if none exists.
    """
    if not course.module_set.exists():
        # Create a default module
        default_module = Module.objects.create(
            course=course,
            name=f"Module 1: Introduction to {course.name}",
            description="This is the first module of the course.",
            order=1
        )
        return default_module
    return None


def get_course_content_statistics(course):
    """
    Get comprehensive statistics about course content
    """
    stats = {
        'total_modules': 0,
        'total_videos': 0,
        'total_pdfs': 0,
        'total_notes': 0,
        'total_quizzes': 0,
        'total_assignments': 0,
        'total_exams': 0,
        'total_content': 0
    }
    
    # Count modules
    modules = course.module_set.all()
    stats['total_modules'] = modules.count()
    
    # Count module content
    for module in modules:
        if module.video:
            stats['total_videos'] += 1
        if module.pdf:
            stats['total_pdfs'] += 1
        if module.note:
            stats['total_notes'] += 1
        
        # Module quizzes and assignments
        stats['total_quizzes'] += module.module_quizzes.filter(is_active=True).count()
        stats['total_assignments'] += module.module_assignments.filter(is_active=True).count()
        stats['total_exams'] += module.module_exams.filter(is_active=True).count() if hasattr(module, 'module_exams') else 0
    
    # Course-level content
    stats['total_quizzes'] += course.course_quizzes.filter(is_active=True).count()
    stats['total_assignments'] += course.assignments.filter(is_active=True).count()
    stats['total_exams'] += course.exams.filter(is_active=True).count() if hasattr(course, 'exams') else 0
    
    # Total content
    stats['total_content'] = (stats['total_videos'] + stats['total_pdfs'] + 
                             stats['total_notes'] + stats['total_quizzes'] + 
                             stats['total_assignments'] + stats['total_exams'])
    
    return stats


def get_user_course_progress_detailed(user, course):
    """
    Get detailed progress information for a user in a course
    """
    try:
        enrollment = Enrollment.objects.get(student=user, course=course)
        
        # Get content statistics
        stats = get_course_content_statistics(course)
        
        # Get completed content counts by type
        completed_videos = len(get_completed_content_ids(user, course, 'video'))
        completed_pdfs = len(get_completed_content_ids(user, course, 'pdf'))
        completed_notes = len(get_completed_content_ids(user, course, 'note'))
        completed_quizzes = len(get_completed_content_ids(user, course, 'quiz'))
        completed_assignments = len(get_completed_content_ids(user, course, 'assignment'))
        
        total_completed = (completed_videos + completed_pdfs + completed_notes + 
                          completed_quizzes + completed_assignments)
        
        return {
            'enrollment': enrollment,
            'progress_percentage': enrollment.progress,
            'total_content': stats['total_content'],
            'completed_content': total_completed,
            'stats': stats,
            'completed_by_type': {
                'videos': completed_videos,
                'pdfs': completed_pdfs,
                'notes': completed_notes,
                'quizzes': completed_quizzes,
                'assignments': completed_assignments,
            }
        }
        
    except Enrollment.DoesNotExist:
        return None
