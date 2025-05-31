from django.db.models import Q, Count, Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
from .models import Course, Module, Video, Comment, SubComment, Notes, Monitor, Tags, Quiz, Question, Answer, Enrollment, VideoProgress, Assignment, AssignmentSubmission, UserExamAttempt, ContentProgress
from user.models import Profile, Student, Organization, Teacher


def searchCourses(request):
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
    Uses the new ContentProgress model for accurate tracking
    """
    course = enrollment.course
    student = enrollment.student
    
    print(f"[DEBUG] Updating progress for {student.username} in course {course.name}")
    
    # Count total content items in the course
    total_videos = Video.objects.filter(module__course=course).count()
    total_notes = Notes.objects.filter(module__course=course).count()
    
    # Count module PDFs and additional materials
    modules_with_pdf = Module.objects.filter(course=course, module_pdf__isnull=False).count()
    modules_with_additional = Module.objects.filter(course=course, additional_materials__isnull=False).count()
    total_notes += modules_with_pdf + modules_with_additional
    
    total_quizzes = Quiz.objects.filter(course=course).count()
    total_assignments = Assignment.objects.filter(course=course).count()
    
    total_content_items = total_videos + total_notes + total_quizzes + total_assignments
    
    print(f"[DEBUG] Content counts - Videos: {total_videos}, Notes: {total_notes}, Quizzes: {total_quizzes}, Assignments: {total_assignments}")
    print(f"[DEBUG] Total content items: {total_content_items}")
    
    if total_content_items == 0:
        enrollment.progress = 100.0
        enrollment.status = 'completed'
        enrollment.save(update_fields=['progress', 'status'])
        return 100.0
    
    # Count completed items using ContentProgress
    completed_count = ContentProgress.objects.filter(
        user=student,
        course=course,
        completed=True
    ).count()
    
    print(f"[DEBUG] Completed items from ContentProgress: {completed_count}")
    
    # If no entries in ContentProgress, try to migrate from old systems
    if completed_count == 0:
        print("[DEBUG] No ContentProgress entries found, migrating from old systems...")
        
        # Migrate video progress
        completed_videos = VideoProgress.objects.filter(
            student=student,
            video__module__course=course,
            watched=True
        )
        for video_progress in completed_videos:
            ContentProgress.objects.get_or_create(
                user=student,
                course=course,
                content_type='video',
                content_id=str(video_progress.video.id),
                defaults={'completed': True}
            )
        
        # Migrate quiz progress
        try:
            completed_quiz_attempts = UserExamAttempt.objects.filter(
                user=student,
                exam__course=course,
                passed=True
            )
            for attempt in completed_quiz_attempts:
                ContentProgress.objects.get_or_create(
                    user=student,
                    course=course,
                    content_type='quiz',
                    content_id=str(attempt.exam.id),
                    defaults={'completed': True}
                )
        except Exception as e:
            print(f"[DEBUG] Error migrating quiz progress: {e}")
        
        # Migrate assignment progress
        try:
            completed_assignment_submissions = AssignmentSubmission.objects.filter(
                user=student,
                assignment__course=course,
                status__in=['submitted', 'graded']
            )
            for submission in completed_assignment_submissions:
                ContentProgress.objects.get_or_create(
                    user=student,
                    course=course,
                    content_type='assignment',
                    content_id=str(submission.assignment.id),
                    defaults={'completed': True}
                )
        except Exception as e:
            print(f"[DEBUG] Error migrating assignment progress: {e}")
        
        # Recount after migration
        completed_count = ContentProgress.objects.filter(
            user=student,
            course=course,
            completed=True
        ).count()
        print(f"[DEBUG] Completed items after migration: {completed_count}")
    
    # Calculate progress percentage
    if total_content_items > 0:
        progress = round((completed_count / total_content_items) * 100, 1)
        enrollment.progress = min(progress, 100.0)  # Cap at 100%
    else:
        enrollment.progress = 100.0
    
    print(f"[DEBUG] Calculated progress: {enrollment.progress}%")
    
    # Update enrollment
    enrollment.last_accessed = timezone.now()
    
    # Mark as completed if 90% or higher
    if enrollment.progress >= 90 or enrollment.status == 'completed':
        enrollment.status = 'completed'
        if enrollment.progress < 100:
            enrollment.progress = 100.0  # Round up to 100% when completed
    
    enrollment.save(update_fields=['progress', 'last_accessed', 'status'])
    print(f"[DEBUG] Final progress saved: {enrollment.progress}%")
    
    return enrollment.progress


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