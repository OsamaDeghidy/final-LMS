from django.db.models import Q, Count, Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
from .models import Course, Module, Video, Comment, SubComment, Notes, Monitor, Tags, Quiz, Question, Answer, Enrollment, VideoProgress
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
    """
    course = enrollment.course
    student = enrollment.student
    
    # Get total number of videos in the course
    total_videos = Video.objects.filter(module__course=course).count()
    
    if total_videos == 0:
        # No videos to track progress for
        return 0
    
    # Count completed videos using VideoProgress model
    completed_videos = VideoProgress.objects.filter(
        student=student,
        video__module__course=course,
        watched=True
    ).count()
    
    # Calculate progress percentage
    if total_videos > 0:
        progress = (completed_videos / total_videos) * 100
        enrollment.progress = progress
    
    # Update last accessed time
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['progress', 'last_accessed'])
    
    # Check if course is completed
    if progress >= 100 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.save(update_fields=['status'])
    
    return enrollment.progress


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