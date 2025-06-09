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
    Uses the ContentProgress model for tracking completion of course materials
    """
    try:
        course = enrollment.course
        student = enrollment.student
        
        print(f"[DEBUG] Updating progress for {student.username} in course {course.name}")
        
        # Count total content items in the course
        total_notes = Notes.objects.filter(module__course=course).count()
        
        # Count module PDFs and additional materials
        modules_with_pdf = Module.objects.filter(course=course, module_pdf__isnull=False).count()
        modules_with_additional = Module.objects.filter(course=course, additional_materials__isnull=False).count()
        total_notes += modules_with_pdf + modules_with_additional
        
        total_quizzes = Quiz.objects.filter(module__course=course).count()
        total_assignments = Assignment.objects.filter(module__course=course).count()
        
        total_content_items = total_notes + total_quizzes + total_assignments
        
        print(f"[DEBUG] Content counts - Notes: {total_notes}, Quizzes: {total_quizzes}, "
              f"Assignments: {total_assignments}")
        print(f"[DEBUG] Total content items: {total_content_items}")
        
        if total_content_items == 0:
            enrollment.progress = 0.0  # Set to 0 when no content
            enrollment.status = 'in_progress'
            enrollment.save(update_fields=['progress', 'status'])
            return 0.0
        
        # Get all content item IDs for this course
        note_ids = list(Notes.objects.filter(module__course=course).values_list('id', flat=True))
        quiz_ids = list(Quiz.objects.filter(module__course=course).values_list('id', flat=True))
        assignment_ids = list(Assignment.objects.filter(module__course=course).values_list('id', flat=True))
        
        # Count completed items using ContentProgress
        completed_count = ContentProgress.objects.filter(
            user=student,
            completed=True,
            content_id__in=note_ids + quiz_ids + assignment_ids
        ).count()
        
        print(f"[DEBUG] Completed items from ContentProgress: {completed_count}")
        
        # Calculate progress percentage
        progress = (completed_count / total_content_items * 100) if total_content_items > 0 else 0
        progress = round(progress, 2)
        
        # Update enrollment status based on progress
        if progress >= 100:
            status = 'completed'
        elif progress > 0:
            status = 'in_progress'
        else:
            status = 'not_started'
        
        # Save the updated progress and status
        enrollment.progress = progress
        enrollment.status = status
        enrollment.last_accessed = timezone.now()
        
        # Mark as completed if 90% or higher
        if progress >= 90 or status == 'completed':
            enrollment.status = 'completed'
            if progress < 100:
                enrollment.progress = 100.0  # Round up to 100% when completed
        
        enrollment.save(update_fields=['progress', 'status', 'last_accessed'])
        print(f"[DEBUG] Final progress saved: {enrollment.progress}%")
        
        # Update course progress if needed
        try:
            update_course_progress(student, course)
        except Exception as e:
            print(f"[ERROR] Error updating course progress: {e}")
        
        return enrollment.progress
        
    except Exception as e:
        print(f"[ERROR] Error in update_enrollment_progress: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def mark_content_completed(user, course, content_type, content_id):
    """
    Mark a specific content item as completed
    """
    progress_item, created = ContentProgress.objects.get_or_create(
        user=user,
        course=course,
        content_type=content_type,
        content_id=str(content_id),
        defaults={'completed': True}
    )
    
    if not created and not progress_item.completed:
        progress_item.completed = True
        progress_item.save(update_fields=['completed'])
    
    print(f"[DEBUG] Marked {content_type} {content_id} as completed for {user.username}")
    
    # Update enrollment progress
    try:
        enrollment = Enrollment.objects.get(student=user, course=course)
        return update_enrollment_progress(enrollment)
    except Enrollment.DoesNotExist:
        return 0


def get_completed_content_ids(user, course, content_type):
    """
    Get list of completed content IDs for a specific type
    """
    completed_ids = ContentProgress.objects.filter(
        user=user,
        course=course,
        content_type=content_type,
        completed=True
    ).values_list('content_id', flat=True)
    
    # Convert to integers for compatibility
    return [int(content_id) for content_id in completed_ids if content_id.isdigit()]


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
