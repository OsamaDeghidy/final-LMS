from django.db.models import Q, Count, Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
from .models import Course, Module, Video, Comment, SubComment, Notes, Monitor, Tags, Quiz, Question, Answer, Enrollment, VideoProgress, Assignment, AssignmentSubmission, UserExamAttempt
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
    Includes videos, quizzes, PDFs, and assignments in the progress calculation
    """
    course = enrollment.course
    student = enrollment.student
    
    # Get total number of content items in the course
    total_videos = Video.objects.filter(module__course=course).count()
    
    try:
        total_quizzes = Quiz.objects.filter(course=course).count()
    except:
        total_quizzes = 0
        
    try:
        total_pdfs = Notes.objects.filter(course=course).count()
    except:
        total_pdfs = 0
        
    try:
        total_assignments = Assignment.objects.filter(course=course).count()
    except:
        total_assignments = 0
    
    total_content_items = total_videos + total_quizzes + total_pdfs + total_assignments
    
    if total_content_items == 0:
        # No content to track progress for
        return 0
    
    # Count completed videos
    completed_videos = VideoProgress.objects.filter(
        student=student,
        video__module__course=course,
        watched=True
    ).count()
    
    # Count completed quizzes
    try:
        completed_quizzes = UserExamAttempt.objects.filter(
            user=student,
            exam__course=course,
            passed=True
        ).count()
    except:
        completed_quizzes = 0
    
    # Count accessed PDFs (Notes)
    try:
        # For now, assume no PDFs are completed since we don't have the PDFAccess table yet
        # In a real implementation, you would track PDF views
        completed_pdfs = 0
    except Exception as e:
        print(f"Error counting PDFs: {e}")
        completed_pdfs = 0
    
    # Count completed assignments
    try:
        completed_assignments = AssignmentSubmission.objects.filter(
            user=student,
            assignment__course=course,
            status='graded'
        ).count()
    except:
        completed_assignments = 0
    
    # Calculate total completed items
    total_completed = completed_videos + completed_quizzes + completed_pdfs + completed_assignments
    
    # Calculate progress percentage
    if total_content_items > 0:
        progress = (total_completed / total_content_items) * 100
        enrollment.progress = min(progress, 100)  # Cap at 100%
    
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