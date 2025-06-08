from django.shortcuts import render, redirect, get_object_or_404
import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from website.models import (
    Course, Module, Video, Notes, Quiz, 
    Assignment, Enrollment, VideoProgress, 
    ContentProgress, PDFAccess, Exam
)
from website.utils import (
    update_enrollment_progress, mark_content_completed,
    get_completed_content_ids, get_user_course_progress
)

import logging
logger = logging.getLogger(__name__)

@login_required
def course_list(request):
    """Display all available courses"""
    # Get filter parameters
    category_id = request.GET.get('category')
    level = request.GET.get('level')
    search_query = request.GET.get('search', '')
    
    # Start with all published courses
    courses = Course.objects.filter(status='published')
    
    # Apply filters
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    if level:
        courses = courses.filter(level=level)
    
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(small_description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Get all categories for filter dropdown
    from website.models import Category
    categories = Category.objects.all()
    
    # Get user enrollments to mark enrolled courses
    if request.user.is_authenticated:
        enrolled_courses = Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)
    else:
        enrolled_courses = []
    
    context = {
        'courses': courses,
        'categories': categories,
        'enrolled_courses': enrolled_courses,
        'selected_category': category_id,
        'selected_level': level,
        'search_query': search_query,
    }
    
    return render(request, 'website/courses/course_list.html', context)

@login_required
def course_detail(request, course_id):
    """Display detailed information about a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    is_enrolled = False
    enrollment = None
    progress = 0
    
    if request.user.is_authenticated:
        try:
            enrollment = Enrollment.objects.get(course=course, student=request.user)
            is_enrolled = True
            progress = enrollment.progress
        except Enrollment.DoesNotExist:
            pass
    
    # Get course modules with content counts
    modules = Module.objects.filter(course=course).prefetch_related(
        'video_set', 'notes_set', 'quiz_set'
    ).order_by('number')
    
    # Get course assignments
    assignments = Assignment.objects.filter(course=course).order_by('due_date')
    
    # Get course exams
    exams = Exam.objects.filter(course=course)
    
    # Get course reviews
    from website.models import Review
    reviews = Review.objects.filter(course=course).select_related('user')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'progress': progress,
        'modules': modules,
        'assignments': assignments,
        'exams': exams,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'website/courses/course_detail.html', context)

@login_required
def course_content(request, course_id):
    """Display the course content page with modules, videos, PDFs, etc."""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    # Update last accessed time
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['last_accessed'])
    
    # Get all modules with their content
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Get completed content IDs
    completed_videos = get_completed_content_ids(request.user, course, 'video')
    completed_notes = get_completed_content_ids(request.user, course, 'note')
    completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
    completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
    
    # Get current content if specified
    current_content = None
    content_type = request.GET.get('type')
    content_id = request.GET.get('id')
    
    if content_type and content_id:
        if content_type == 'video':
            video = get_object_or_404(Video, id=content_id, module__course=course)
            current_content = {
                'type': 'video',
                'object': video,
                'completed': int(video.id) in completed_videos
            }
        elif content_type == 'note':
            note = get_object_or_404(Notes, id=content_id, module__course=course)
            current_content = {
                'type': 'note',
                'object': note,
                'completed': int(note.id) in completed_notes
            }
            # Mark PDF as accessed
            PDFAccess.objects.get_or_create(
                user=request.user,
                pdf_id=note.id,
                defaults={'read': True}
            )
        elif content_type == 'quiz':
            quiz = get_object_or_404(Quiz, id=content_id, course=course)
            current_content = {
                'type': 'quiz',
                'object': quiz,
                'completed': int(quiz.id) in completed_quizzes
            }
        elif content_type == 'assignment':
            assignment = get_object_or_404(Assignment, id=content_id, course=course)
            current_content = {
                'type': 'assignment',
                'object': assignment,
                'completed': int(assignment.id) in completed_assignments
            }
        elif content_type == 'module_pdf':
            module = get_object_or_404(Module, id=content_id, course=course)
            if module.module_pdf:
                current_content = {
                    'type': 'module_pdf',
                    'object': module,
                    'completed': False  # We'll implement tracking for this later
                }
                # Mark module PDF as accessed
                PDFAccess.objects.get_or_create(
                    user=request.user,
                    pdf_id=int(f"1{module.id}"),  # Use prefix to avoid ID conflicts
                    defaults={'read': True}
                )
    
    # If no content is specified, find the first incomplete video
    if not current_content:
        # First try to find an incomplete video
        for module in modules:
            videos = Video.objects.filter(module=module).order_by('number')
            for video in videos:
                if int(video.id) not in completed_videos:
                    current_content = {
                        'type': 'video',
                        'object': video,
                        'completed': False
                    }
                    break
            if current_content:
                break
        
        # If all videos are complete or there are no videos, show the first module's content
        if not current_content and modules.exists():
            first_module = modules.first()
            videos = Video.objects.filter(module=first_module).order_by('number')
            if videos.exists():
                current_content = {
                    'type': 'video',
                    'object': videos.first(),
                    'completed': int(videos.first().id) in completed_videos
                }
            elif first_module.module_pdf:
                current_content = {
                    'type': 'module_pdf',
                    'object': first_module,
                    'completed': False
                }
    
    context = {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'current_content': current_content,
        'completed_videos': completed_videos,
        'completed_notes': completed_notes,
        'completed_quizzes': completed_quizzes,
        'completed_assignments': completed_assignments,
    }
    
    return render(request, 'website/courses/course_content.html', context)

@login_required
def module_pdf_view(request, course_id, module_id):
    """View a module's PDF file"""
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    if not module.module_pdf:
        messages.error(request, 'لا يوجد ملف PDF لهذا الموديول')
        return redirect('courses:course_content', course_id=course_id)
    
    # Mark PDF as accessed
    PDFAccess.objects.get_or_create(
        user=request.user,
        pdf_id=int(f"1{module.id}"),  # Use prefix to avoid ID conflicts
        defaults={'read': True}
    )
    
    # Mark as completed in ContentProgress
    mark_content_completed(request.user, course, 'module_pdf', module.id)
    
    context = {
        'course': course,
        'module': module,
        'pdf_url': module.module_pdf.url,
    }
    
    return render(request, 'website/courses/module_pdf_view.html', context)

@login_required
def course_materials_view(request, course_id):
    """View a course's materials PDF file"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    if not course.materials_pdf:
        messages.error(request, 'لا يوجد ملف مواد إضافية لهذه الدورة')
        return redirect('courses:course_content', course_id=course_id)
    
    # Mark PDF as accessed
    PDFAccess.objects.get_or_create(
        user=request.user,
        pdf_id=int(f"2{course.id}"),  # Use prefix to avoid ID conflicts
        defaults={'read': True}
    )
    
    # Mark as completed in ContentProgress
    mark_content_completed(request.user, course, 'course_materials', course.id)
    
    context = {
        'course': course,
        'pdf_url': course.materials_pdf.url,
    }
    
    return render(request, 'website/courses/course_materials_view.html', context)

@login_required
def course_syllabus_view(request, course_id):
    """View a course's syllabus PDF file"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    if not course.syllabus_pdf:
        messages.error(request, 'لا يوجد ملف منهج لهذه الدورة')
        return redirect('courses:course_content', course_id=course_id)
    
    # Mark PDF as accessed
    PDFAccess.objects.get_or_create(
        user=request.user,
        pdf_id=int(f"3{course.id}"),  # Use prefix to avoid ID conflicts
        defaults={'read': True}
    )
    
    # Mark as completed in ContentProgress
    mark_content_completed(request.user, course, 'course_syllabus', course.id)
    
    context = {
        'course': course,
        'pdf_url': course.syllabus_pdf.url,
    }
    
    return render(request, 'website/courses/course_syllabus_view.html', context)

@login_required
@require_POST
def mark_content_viewed(request, content_type, content_id):
    """API endpoint to mark content as viewed/completed"""
    course_id = request.POST.get('course_id')
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'غير مسجل في الدورة'}, status=403)
    
    # Mark content as completed
    progress = mark_content_completed(request.user, course, content_type, content_id)
    
    return JsonResponse({
        'status': 'success',
        'message': 'تم تحديث التقدم',
        'progress': progress
    })

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def mark_pdf_read(request):
    """
    API endpoint to mark a PDF as read for the current user.
    Expects JSON data with 'pdf_id' and 'course_id'.
    """
    try:
        data = json.loads(request.body)
        pdf_id = data.get('pdf_id')
        course_id = data.get('course_id')
        
        if not pdf_id or not course_id:
            return JsonResponse(
                {'success': False, 'error': 'Missing pdf_id or course_id'}, 
                status=400
            )
        
        # Get the course
        course = get_object_or_404(Course, id=course_id)
        
        # Mark the PDF as accessed
        pdf_access, created = PDFAccess.objects.get_or_create(
            user=request.user,
            pdf_id=pdf_id,
            defaults={'read': True, 'access_date': timezone.now()}
        )
        
        if not created and not pdf_access.read:
            pdf_access.read = True
            pdf_access.access_date = timezone.now()
            pdf_access.save()
        
        # Mark the content as completed in the progress tracking
        mark_content_completed(request.user, course, 'module_pdf', pdf_id)
        
        # Update the course progress
        update_enrollment_progress(request.user, course)
        
        return JsonResponse({
            'success': True,
            'message': 'تم تحديد الملف كمقروء بنجاح',
            'pdf_id': pdf_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error marking PDF as read: {str(e)}")
        return JsonResponse(
            {'success': False, 'error': 'حدث خطأ أثناء معالجة الطلب'}, 
            status=500
        )

@login_required
def course_assignments(request, course_id):
    """View all assignments for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    # Get all assignments
    assignments = Assignment.objects.filter(course=course).order_by('due_date')
    
    # Get user submissions
    from website.models import AssignmentSubmission
    submissions = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment__course=course
    ).select_related('assignment')
    
    # Create a dict of assignment_id -> submission for easy lookup
    submission_dict = {sub.assignment.id: sub for sub in submissions}
    
    context = {
        'course': course,
        'assignments': assignments,
        'submission_dict': submission_dict,
    }
    
    return render(request, 'website/courses/course_assignments.html', context)

@login_required
def course_exams(request, course_id):
    """View all exams for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, 'يجب التسجيل في الدورة أولاً للوصول إلى المحتوى')
        return redirect('courses:course_detail', course_id=course_id)
    
    # Get all exams
    exams = Exam.objects.filter(course=course)
    
    # Get user attempts
    from website.models import UserExamAttempt
    attempts = UserExamAttempt.objects.filter(
        user=request.user,
        exam__course=course
    ).select_related('exam')
    
    # Create a dict of exam_id -> attempts for easy lookup
    attempt_dict = {}
    for attempt in attempts:
        if attempt.exam.id not in attempt_dict:
            attempt_dict[attempt.exam.id] = []
        attempt_dict[attempt.exam.id].append(attempt)
    
    context = {
        'course': course,
        'exams': exams,
        'attempt_dict': attempt_dict,
    }
    
    return render(request, 'website/courses/course_exams.html', context)

@login_required
def recalculate_progress(request, course_id):
    """API endpoint to recalculate course progress"""
    course = get_object_or_404(Course, id=course_id)
    
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
        progress = update_enrollment_progress(enrollment)
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم إعادة حساب التقدم بنجاح',
            'progress': progress
        })
    except Enrollment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'غير مسجل في الدورة'
        }, status=403)
    except Exception as e:
        logger.error(f"Error recalculating progress: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)
