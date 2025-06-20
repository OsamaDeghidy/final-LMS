from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import logging
from django.db.models import Avg

from .models import (
    Category, Course, Module, Tags, Quiz, Question, Answer, Enrollment, 
    Review, Cart, CartItem, Assignment, AssignmentSubmission, UserExamAttempt, 
    ContentProgress, Article, UserProgress, ModuleProgress, CourseProgress,
    Comment, SubComment, CommentLike, SubCommentLike, Exam, ExamQuestion, ExamAnswer,
    QuizAttempt, QuizUserAnswer, CourseReview, ReviewReply, Certificate, CertificateTemplate
)
from user.models import Profile, Student, Organization, Teacher
from .utils_course import searchCourses, update_enrollment_progress, mark_content_completed, get_completed_content_ids, get_user_course_progress, get_user_enrolled_courses, ensure_course_has_module
from .decorators import student_required

def find_next_content_url(course, current_type, current_id, user):
    """Find the next content item after the current one"""
    try:
        # Get all modules for this course with prefetch for better performance
        modules = Module.objects.filter(course=course).order_by('number')
        
        # Build navigation for next content
        all_content = []
        
        for module in modules:
            # Add video content
            if module.video:
                all_content.append({
                    'type': 'module_video',
                    'id': str(module.id),
                    'url': f'/courseviewpage/{course.id}/?content_type=module_video&content_id={module.id}',
                    'title': f'فيديو: {module.name}'
                })
            
            # Add PDF content
            if module.pdf:
                all_content.append({
                    'type': 'module_pdf', 
                    'id': str(module.id),
                    'url': f'/courseviewpage/{course.id}/?content_type=module_pdf&content_id={module.id}',
                    'title': f'PDF: {module.name}'
                })
            
            # Add notes content
            if module.note:
                all_content.append({
                    'type': 'module_note',
                    'id': str(module.id),
                    'url': f'/courseviewpage/{course.id}/?content_type=module_note&content_id={module.id}',
                    'title': f'ملاحظات: {module.name}'
                })
            
            # Add module quizzes
            for quiz in module.module_quizzes.filter(is_active=True).order_by('created_at'):
                all_content.append({
                    'type': 'quiz',
                    'id': str(quiz.id),
                    'url': f'/courseviewpage/{course.id}/?content_type=quiz&content_id={quiz.id}',
                    'title': quiz.title or f'اختبار: {module.name}'
                })
            
            # Add module assignments
            for assignment in module.module_assignments.filter(is_active=True).order_by('created_at'):
                all_content.append({
                    'type': 'assignment',
                    'id': str(assignment.id),
                    'url': f'/courseviewpage/{course.id}/?content_type=assignment&content_id={assignment.id}',
                    'title': assignment.title
                })
        
        # Add course-level quizzes
        for quiz in course.course_quizzes.filter(is_active=True).order_by('created_at'):
            all_content.append({
                'type': 'quiz',
                'id': str(quiz.id),
                'url': f'/courseviewpage/{course.id}/?content_type=quiz&content_id={quiz.id}',
                'title': quiz.title
            })
        
        # Add course-level assignments
        for assignment in course.assignments.filter(is_active=True).order_by('created_at'):
            all_content.append({
                'type': 'assignment',
                'id': str(assignment.id),
                'url': f'/courseviewpage/{course.id}/?content_type=assignment&content_id={assignment.id}',
                'title': assignment.title
            })
        
        # Find current content index
        current_index = -1
        for i, content in enumerate(all_content):
            if content['type'] == current_type and content['id'] == str(current_id):
                current_index = i
                break
        
        # Get next content
        if current_index >= 0 and current_index < len(all_content) - 1:
            next_content = all_content[current_index + 1]
            return next_content['url']
        
        return None
        
    except Exception as e:
        print(f"Error finding next content: {e}")
        return None

# Set up logging
logger = logging.getLogger(__name__)

# Course listing views
@login_required
def allcourses(request):
    courses, search_query = searchCourses(request)
    context = {'courses': courses, 'search_query': search_query}
    return render(request, 'website/courses/allcourses.html', context)

def course_category(request, category_slug):
    # Get the category or return 404 if not found
    category = get_object_or_404(Category, name=category_slug)
    
    # Get all courses in this category
    courses = Course.objects.filter(category=category, status='published')
    
    # Get all articles in this category (only those with valid slugs)
    articles = Article.objects.filter(category=category, status='published', slug__isnull=False).exclude(slug='')
    
    # Get all categories with their content for the new template structure
    all_categories = Category.objects.all().order_by('name')
    all_courses = Course.objects.filter(status='published').order_by('-created_at')
    all_articles = Article.objects.filter(status='published', slug__isnull=False).exclude(slug='').order_by('-created_at')
    
    # Create categories structure for the new template
    categories_with_content = []
    for cat in all_categories:
        cat_courses = all_courses.filter(category=cat)
        cat_articles = all_articles.filter(category=cat)
        
        categories_with_content.append({
            'category': cat,
            'courses': cat_courses,
            'articles': cat_articles,
            'total_content': cat_courses.count() + cat_articles.count(),
        })
    
    context = {
        'category': category,
        'courses': courses,
        'articles': articles,
        # New structure for the updated template
        'categories': categories_with_content,
        'all_courses': all_courses,
        'all_articles': all_articles,
        'total_all_content': all_courses.count() + all_articles.count(),
    }
    
    return render(request, 'website/category_courses.html', context)

def categories_view(request):
    """
    عرض جميع التصنيفات مع محتوياتها (كورسات، مقالات، إلخ)
    """
    # Get all categories
    categories = Category.objects.all().order_by('name')
    
    # Get all published courses
    all_courses = Course.objects.filter(status='published').order_by('-created_at')
    
    # Get all published articles (only those with valid slugs)
    all_articles = Article.objects.filter(status='published', slug__isnull=False).exclude(slug='').order_by('-created_at')
    
    # Create a dictionary to store content for each category
    categories_with_content = []
    
    for category in categories:
        # Get courses for this category
        category_courses = all_courses.filter(category=category)
        
        # Get articles for this category (only those with valid slugs)
        category_articles = all_articles.filter(category=category)
        
        # Add category with its content
        categories_with_content.append({
            'category': category,
            'courses': category_courses,
            'articles': category_articles,
            'total_content': category_courses.count() + category_articles.count(),
        })
    
    # Get all content for "All" tab
    context = {
        'categories': categories_with_content,
        'all_courses': all_courses,
        'all_articles': all_articles,
        'total_all_content': all_courses.count() + all_articles.count(),
    }
    
    return render(request, 'website/simple_categories.html', context)

# Course detail and management views
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Handle review submission (POST request)
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            from user.models import Profile
            profile = Profile.objects.get(user=request.user)
            if profile.status == 'Student':
                is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
                if is_enrolled:
                    rating_value = request.POST.get('review_rating')
                    review_comment = request.POST.get('review_comment', '')
                    
                    if rating_value:
                        try:
                            rating_value = int(rating_value)
                            if 1 <= rating_value <= 5:
                                from .models import Review
                                review, created = Review.objects.update_or_create(
                                    course=course,
                                    user=request.user,
                                    defaults={
                                        'rating': rating_value,
                                        'comment': review_comment
                                    }
                                )
                                if created:
                                    messages.success(request, 'تم إضافة تقييمك بنجاح!')
                                else:
                                    messages.success(request, 'تم تحديث تقييمك بنجاح!')
                            else:
                                messages.error(request, 'التقييم يجب أن يكون بين 1 و 5 نجوم')
                        except ValueError:
                            messages.error(request, 'تقييم غير صالح')
                    else:
                        messages.error(request, 'يجب اختيار تقييم')
                else:
                    messages.error(request, 'يجب أن تكون مسجلاً في الدورة لإضافة تقييم')
            else:
                messages.error(request, 'التقييم متاح للطلاب فقط')
        except Profile.DoesNotExist:
            messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم')
        
        return redirect('course_detail', course_id=course_id)
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    
    # Check user type for permissions
    is_student = False
    is_teacher = False
    is_admin = False
    user_profile = None
    
    if request.user.is_authenticated:
        try:
            from user.models import Profile
            user_profile = Profile.objects.get(user=request.user)
            is_student = user_profile.status == 'Student'
            is_teacher = user_profile.status == 'Teacher'
            is_admin = user_profile.status == 'Admin'
        except Profile.DoesNotExist:
            pass
    
    # Check if course is in cart (only for students)
    in_cart = False
    if is_student:
        try:
            from .models import Cart, CartItem
            cart = Cart.objects.get(user=request.user)
            in_cart = CartItem.objects.filter(cart=cart, course=course).exists()
        except Cart.DoesNotExist:
            pass
    
    # Get user review (only for students)
    user_review = None
    if is_student and is_enrolled:
        try:
            from .models import Review
            user_review = Review.objects.get(course=course, user=request.user)
        except Review.DoesNotExist:
            pass
    
    # Get all reviews for the course
    from .models import Review
    reviews = Review.objects.filter(course=course).select_related('user').order_by('-created_at')
    
    # Get final exams for the course
    final_exams = course.exams.filter(is_final=True, is_active=True).order_by('created_at')
    
    # Get course-level assignments (not module-specific)
    course_assignments = course.assignments.filter(module__isnull=True, is_active=True).order_by('created_at')
    
    # Get course-level quizzes (not module-specific)
    course_quizzes = course.course_quizzes.filter(module__isnull=True, is_active=True).order_by('created_at')
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'is_admin': is_admin,
        'user_profile': user_profile,
        'in_cart': in_cart,
        'user_review': user_review,
        'reviews': reviews,
        'final_exams': final_exams,
        'course_assignments': course_assignments,
        'course_quizzes': course_quizzes,
    }
    
    return render(request, 'website/courses/course_detail.html', context)

@login_required
def course(request):
    # Redirect to dashboard instead of showing course list
    from django.shortcuts import redirect
    return redirect('dashboard')

# Course viewing pages
@login_required
def courseviewpage(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, _('You are not enrolled in this course.'))
        return redirect('course_detail', course_id=course_id)
    
    # Get all modules for this course with prefetch for better performance
    modules = Module.objects.filter(course=course).prefetch_related(
        'module_quizzes__questions',
        'module_assignments'
    ).order_by('number')
    
    # Update last accessed time
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['last_accessed'])
    
    # ============ استخدام نظام Progress الجديد ============
    # Get user progress using the new system
    try:
        user_progress = course.get_user_progress(request.user)
        progress_percentage = user_progress.overall_progress
        modules_with_progress = course.get_modules_with_progress(request.user)
        next_module = course.get_next_module_for_user(request.user)
    except Exception as e:
        logger.error(f"Error getting progress for user {request.user.id} in course {course_id}: {e}")
        # Fallback to old system
        progress_percentage = enrollment.progress or 0
        modules_with_progress = []
        next_module = None
    
    # ============ نظام المحتوى المحسن ============
    # Get completed content IDs for progress tracking (keep for backward compatibility)
    completed_videos = get_completed_content_ids(request.user, course, 'video')
    completed_notes = get_completed_content_ids(request.user, course, 'note')
    completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
    completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
    completed_pdfs = get_completed_content_ids(request.user, course, 'pdf')
    
    # Calculate comprehensive statistics
    total_videos = 0
    total_notes = 0
    total_pdfs = 0
    total_quizzes = 0
    assignments_count = 0
    
    # Count module-level content
    for module in modules:
        if module.video:
            total_videos += 1
        if module.pdf:
            total_pdfs += 1
        if module.note:
            total_notes += 1
        # Count active quizzes and assignments for this module
        total_quizzes += module.module_quizzes.filter(is_active=True).count()
        assignments_count += module.module_assignments.filter(is_active=True).count()
    
    # Add course-level quizzes and assignments
    course_quizzes = course.course_quizzes.filter(is_active=True)
    course_assignments = course.assignments.filter(is_active=True)
    
    total_quizzes += course_quizzes.count()
    assignments_count += course_assignments.count()
    
    # Calculate total reading materials (PDFs + Notes)
    total_reading = total_pdfs + total_notes
    
    # Calculate progress more accurately (backup calculation)
    total_content = total_videos + total_reading + total_quizzes + assignments_count
    completed_content = (len(completed_videos) + len(completed_notes) + 
                        len(completed_pdfs) + len(completed_quizzes) + 
                        len(completed_assignments))
    
    if total_content > 0:
        fallback_progress = (completed_content / total_content) * 100
    else:
        fallback_progress = 0
    
    # Use new progress system, fallback to old calculation if needed
    if progress_percentage is None or progress_percentage == 0:
        progress_percentage = fallback_progress
    
    # Update enrollment progress
    enrollment.progress = progress_percentage
    enrollment.save(update_fields=['progress'])
    
    # Check if specific content is requested via URL parameters
    content_type = request.GET.get('content_type')
    content_id = request.GET.get('content_id')
    
    current_content = None
    next_content = None
    prev_content = None
    first_available_content = None
    current_module_progress = None
    
    if content_type and content_id:
        try:
            if content_type == 'module_pdf' or content_type == 'pdf':
                # Get the module with the PDF file
                module = Module.objects.get(id=int(content_id), course=course)
                if module.pdf:
                    current_content = {
                        'type': 'module_pdf',
                        'content': module,
                        'module': module,
                        'pdf_url': module.pdf.url,
                        'pdf_title': module.name or f'الوحدة {module.number} - PDF'
                    }
                    # Get module progress for this user
                    current_module_progress = module.get_user_progress(request.user)
                else:
                    messages.error(request, _('PDF file not found for this module.'))
                    
            elif content_type == 'module_video' or content_type == 'video':
                # Get the module's video
                module = Module.objects.get(id=int(content_id), course=course)
                if module.video:
                    current_content = {
                        'type': 'module_video',
                        'content': module,
                        'module': module,
                        'video_url': module.video.url,
                        'video_title': module.name or f'الوحدة {module.number} - فيديو'
                    }
                    # Get module progress for this user
                    current_module_progress = module.get_user_progress(request.user)
                else:
                    messages.error(request, _('Video file not found for this module.'))
                    
            elif content_type == 'module_note' or content_type == 'note':
                # Get the module's note
                module = Module.objects.get(id=int(content_id), course=course)
                if module.note:
                    current_content = {
                        'type': 'module_note',
                        'content': module,
                        'module': module,
                        'note_content': module.note,
                        'note_title': module.name or f'الوحدة {module.number} - ملاحظات'
                    }
                    # Get module progress for this user
                    current_module_progress = module.get_user_progress(request.user)
                else:
                    messages.error(request, _('Notes not found for this module.'))
                    
            elif content_type == 'quiz':
                # Get the quiz
                quiz = Quiz.objects.get(id=int(content_id), is_active=True)
                # Check if user has attempts
                user_attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz).order_by('-attempt_number')
                quiz_started = user_attempts.exists()
                
                current_content = {
                    'type': 'quiz',
                    'content': quiz,
                    'quiz': quiz,
                    'questions': quiz.questions.all().order_by('order'),
                    'user_attempts': user_attempts,
                    'quiz_started': quiz_started
                }
                
                # Get module progress if quiz is module-specific
                if quiz.module:
                    current_module_progress = quiz.module.get_user_progress(request.user)
                
            elif content_type == 'assignment':
                # Get the assignment
                assignment = Assignment.objects.get(id=int(content_id), course=course, is_active=True)
                # Get user's submission if exists
                user_submission = None
                if assignment:
                    try:
                        user_submission = AssignmentSubmission.objects.get(
                            assignment=assignment,
                            user=request.user
                        )
                    except AssignmentSubmission.DoesNotExist:
                        pass
                
                current_content = {
                    'type': 'assignment',
                    'content': assignment,
                    'assignment': assignment,
                    'user_submission': user_submission
                }
                
                # Get module progress if assignment is module-specific
                if assignment.module:
                    current_module_progress = assignment.module.get_user_progress(request.user)
                
            elif content_type == 'final_exam':
                # Get the final exam
                exam = Exam.objects.get(id=int(content_id), course=course, is_active=True)
                # Check if user has attempts
                user_attempts = exam.attempts.filter(user=request.user).order_by('-attempt_number')
                
                current_content = {
                    'type': 'final_exam',
                    'content': exam,
                    'exam': exam,
                    'user_attempts': user_attempts,
                    'questions': exam.questions.all().order_by('order')
                }
                
        except (ValueError, Module.DoesNotExist, Quiz.DoesNotExist, 
                Assignment.DoesNotExist, Exam.DoesNotExist) as e:
            messages.error(request, _('Content not found.'))
            return redirect('courseviewpage', course_id=course_id)
    
    # Build navigation for next/previous content
    if current_content:
        # Get all content items in order
        all_content = []
        
        for module in modules:
            # Add video content
            if module.video:
                all_content.append({
                    'type': 'module_video',
                    'content': module,
                    'url': f"?content_type=module_video&content_id={module.id}",
                    'title': f'فيديو: {module.name}'
                })
            
            # Add PDF content
            if module.pdf:
                all_content.append({
                    'type': 'module_pdf', 
                    'content': module,
                    'url': f"?content_type=module_pdf&content_id={module.id}",
                    'title': f'PDF: {module.name}'
                })
            
            # Add notes content
            if module.note:
                all_content.append({
                    'type': 'module_note',
                    'content': module,
                    'url': f"?content_type=module_note&content_id={module.id}",
                    'title': f'ملاحظات: {module.name}'
                })
            
            # Add module quizzes
            for quiz in module.module_quizzes.filter(is_active=True).order_by('created_at'):
                all_content.append({
                    'type': 'quiz',
                    'content': quiz,
                    'url': f"?content_type=quiz&content_id={quiz.id}",
                    'title': quiz.title or f'اختبار: {module.name}'
                })
            
            # Add module assignments
            for assignment in module.module_assignments.filter(is_active=True).order_by('created_at'):
                all_content.append({
                    'type': 'assignment',
                    'content': assignment,
                    'url': f"?content_type=assignment&content_id={assignment.id}",
                    'title': assignment.title
                })
        
        # Add course-level quizzes
        for quiz in course_quizzes.order_by('created_at'):
            all_content.append({
                'type': 'quiz',
                'content': quiz,
                'url': f"?content_type=quiz&content_id={quiz.id}",
                'title': quiz.title or 'اختبار الدورة'
            })
        
        # Add course-level assignments
        for assignment in course_assignments.order_by('created_at'):
            all_content.append({
                'type': 'assignment',
                'content': assignment,
                'url': f"?content_type=assignment&content_id={assignment.id}",
                'title': assignment.title
            })
        
        # Add final exam if exists
        if course.final_exam:
            all_content.append({
                'type': 'final_exam',
                'content': course.final_exam,
                'url': f"?content_type=final_exam&content_id={course.final_exam.id}",
                'title': course.final_exam.title or 'الاختبار النهائي'
            })
        
        # Find current position and set next/prev
        current_index = -1
        for i, item in enumerate(all_content):
            if (item['type'] == current_content['type'] and 
                item['content'].id == current_content['content'].id):
                current_index = i
                break
        
        if current_index >= 0:
            if current_index > 0:
                prev_content = all_content[current_index - 1]
            if current_index < len(all_content) - 1:
                next_content = all_content[current_index + 1]
    
    # Set first available content as current if no content is specified
    first_available_content = None
    if not current_content and modules.exists():
        # Look for first video
        for module in modules:
            if module.video:
                current_content = {
                    'type': 'module_video',
                    'content': module,
                    'module': module,
                    'video_url': module.video.url,
                    'video_title': module.name or f'الوحدة {module.number} - فيديو'
                }
                break
        
        # If no video, look for first PDF
        if not current_content:
            for module in modules:
                if module.pdf:
                    current_content = {
                        'type': 'module_pdf',
                        'content': module,
                        'module': module,
                        'pdf_url': module.pdf.url,
                        'pdf_title': module.name or f'الوحدة {module.number} - PDF'
                    }
                    break
        
        # If no PDF, look for first note
        if not current_content:
            for module in modules:
                if module.note:
                    current_content = {
                        'type': 'module_note',
                        'content': module,
                        'module': module,
                        'note_content': module.note,
                        'note_title': module.name or f'الوحدة {module.number} - ملاحظات'
                    }
                    break
    
    # Get comments for discussion section
    comments = Comment.objects.filter(course=course, is_active=True).select_related('user').prefetch_related(
        'replies__user', 
        'likes',
        'replies__likes'
    ).order_by('-created_at')
    
    # Prepare context with comprehensive data
    # Get course comments
    comments = Comment.objects.filter(course=course).select_related('user').prefetch_related(
        'replies__user', 'likes', 'replies__likes'
    ).order_by('-created_at')
    
    context = {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'is_enrolled': True,
        'completed_videos': completed_videos,
        'completed_notes': completed_notes,
        'completed_assignments': completed_assignments,
        'completed_quizzes': completed_quizzes,
        'completed_pdfs': completed_pdfs,
        'current_content': current_content,
        'next_content': next_content,
        'prev_content': prev_content,
        'progress': progress_percentage,
        'total_videos': total_videos,
        'total_notes': total_reading,  # Combined reading materials
        'total_quizzes': total_quizzes,
        'assignments_count': assignments_count,
        'total_content': total_content,
        'completed_content': completed_content,
        'comments': comments,
        # Additional statistics for better display
        'course_quizzes': course_quizzes,
        'course_assignments': course_assignments,
        'assignments': course_assignments,  # Required for sidebar
        'enrollment_date': enrollment.enrollment_date,
        'last_accessed': enrollment.last_accessed,
        # Discussion section
        'comments': comments,
        'first_available_content': first_available_content,
        # Add missing context variables
        'user_submission': current_content.get('user_submission') if current_content and current_content.get('type') == 'assignment' else None,
        'user_attempt': current_content.get('user_attempts')[0] if current_content and current_content.get('type') == 'final_exam' and current_content.get('user_attempts') else None,
        'quiz_started': current_content.get('quiz_started', False) if current_content and current_content.get('type') == 'quiz' else False,
        'user_attempts': len(current_content.get('user_attempts', [])) if current_content and current_content.get('type') == 'quiz' else 0,
        'current_module_progress': current_module_progress
    }
    
    return render(request, 'website/courses/courseviewpage.html', context)

# Basic course creation and management
@login_required
def create_course(request):
    if request.method == 'POST':
        # Handle form submission
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            learned = request.POST.get('learned')
            small_description = request.POST.get('small_description')
            price = request.POST.get('price', 0)
            category_id = request.POST.get('category')
            level = request.POST.get('level', 'beginner')  # Default to beginner if not provided
            
            # Validate required fields
            if not all([name, description, small_description, category_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'الرجاء ملء جميع الحقول المطلوبة'
                })
            
            # Get or create category
            category = get_object_or_404(Category, id=category_id)
            
            # Get teacher profile
            teacher = None
            try:
                # Get the user's profile
                profile = request.user.profile
                # Get the teacher object through the profile
                if hasattr(profile, 'teacher'):
                    teacher = profile.teacher
                else:
                    # Try to get teacher object if it exists but not linked
                    from user.models import Teacher
                    teacher = Teacher.objects.filter(profile=profile).first()
            except Exception as e:
                print(f"Error getting teacher profile: {e}")
                teacher = None
            
            if not teacher:
                # Check if user has a profile
                if not hasattr(request.user, 'profile'):
                    return JsonResponse({
                        'success': False,
                        'message': 'لم يتم العثور على ملفك الشخصي. يرجى إكمال ملفك الشخصي أولاً.'
                    })
            # Check if user is admin or teacher
            if request.user.profile.status not in ['Admin', 'Teacher']:
                messages.error(request, _('You must be an admin or teacher to create a course.'))
                return redirect('create_course')
                
            # For admin users, ensure they have a teacher profile
            if request.user.profile.status == 'Admin' and not teacher:
                from user.models import Teacher
                teacher = Teacher.objects.create(
                    profile=request.user.profile,
                    bio='System Administrator',
                    qualification='Administrator'
                )
            
            # Create course
            course_data = {
                'name': name,
                'description': description,
                'learned': learned,
                'small_description': small_description,
                'price': price,
                'category_id': category_id,
                'level': level,
                'teacher': teacher,
                'status': 'draft'  # Set initial status as draft
            }
            
            # Create course first without the image to get an ID
            course = Course.objects.create(**course_data)
            
            # Handle course image
            if 'image_course' in request.FILES:
                course.image_course = request.FILES['image_course']
                course.save()
                
            # Handle course PDFs and deletion flags
            if request.POST.get('delete_syllabus_pdf') == '1':
                if course.syllabus_pdf:
                    course.syllabus_pdf.delete()
                    course.syllabus_pdf = None
                    course.save()
            elif 'syllabus_pdf' in request.FILES:
                course.syllabus_pdf = request.FILES['syllabus_pdf']
                course.save()
                
            if request.POST.get('delete_materials_pdf') == '1':
                if course.materials_pdf:
                    course.materials_pdf.delete()
                    course.materials_pdf = None
                    course.save()
            elif 'materials_pdf' in request.FILES:
                course.materials_pdf = request.FILES['materials_pdf']
                course.save()
            
            # Process modules
            module_data = json.loads(request.POST.get('modules', '[]'))
            
            for module in module_data:
                new_module = Module.objects.create(
                    course=course,
                    name=module.get('name'),
                    description=module.get('description'),
                    number=module.get('number')
                )
                
                # Save module video with proper file handling
                video_file = None
                video_title = None
                
                # Check for video file in request.FILES (new format)
                if 'video' in request.FILES:
                    video_file = request.FILES['video']
                    video_title = request.POST.get('video_title', f"Video - {new_module.name}")
                # Fallback to old format
                elif f'module_{module["id"]}_video' in request.FILES:
                    video_file = request.FILES[f'module_{module["id"]}_video']
                    video_title = request.POST.get(f'module_{module["id"]}_video_title', f"Video - {new_module.name}")
                
                if video_file:
                    # Ensure the file is actually a video
                    valid_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
                    if (video_file.content_type and video_file.content_type.startswith('video/')) or \
                       any(video_file.name.lower().endswith(ext) for ext in valid_extensions):
                        try:
                            # Generate a unique filename to avoid conflicts
                            filename = f"{new_module.id}_{video_file.name}"
                            
                            # Set the video on the module
                            new_module.video.save(filename, video_file, save=True)
                            
                            # Store the video title in the module description or as metadata
                            if not new_module.description:
                                new_module.description = f"<p>عنوان الفيديو: {video_title}</p>"
                            else:
                                new_module.description = f"<p>عنوان الفيديو: {video_title}</p>" + new_module.description
                            
                            new_module.save()
                            logger.info(f"Successfully saved video for module {new_module.id}")
                        except Exception as e:
                            logger.error(f"Error saving video for module {new_module.id}: {str(e)}")
                            messages.error(request, f'حدث خطأ أثناء حفظ ملف الفيديو: {str(e)}')
                    else:
                        error_msg = f'نوع ملف الفيديو غير صالح: {getattr(video_file, "content_type", "unknown")}. يجب أن يكون الملف من نوع فيديو (mp4, avi, mov, wmv, flv, mkv, webm)'
                        logger.error(error_msg)
                        messages.error(request, error_msg)
                
                # Process module PDF with proper file handling
                pdf_key = f'module_{module["id"]}_pdf'
                pdf_title_key = f'module_{module["id"]}_pdf_title'
                
                # Check for PDF file in request.FILES
                pdf_file = None
                if pdf_key in request.FILES:
                    pdf_file = request.FILES[pdf_key]
                
                if pdf_file:
                    # Get the PDF title if available
                    pdf_title = request.POST.get(pdf_title_key, f"ملف PDF - {new_module.name}")
                    
                    # Ensure the file is actually a PDF
                    if pdf_file.content_type == 'application/pdf' or pdf_file.name.lower().endswith('.pdf'):
                        try:
                            # Set the PDF on the module
                            new_module.pdf.save(pdf_file.name, pdf_file, save=True)
                            
                            # Store the PDF title in the module description or as metadata
                            if not new_module.description:
                                new_module.description = f"<p>عنوان الملف: {pdf_title}</p>"
                            else:
                                new_module.description = f"<p>عنوان الملف: {pdf_title}</p>" + new_module.description
                                
                            new_module.save()
                            logger.info(f"Successfully saved PDF for module {new_module.id}")
                        except Exception as e:
                            logger.error(f"Error saving PDF for module {new_module.id}: {str(e)}")
                            messages.error(request, f'حدث خطأ أثناء حفظ ملف PDF: {str(e)}')
                    else:
                        messages.error(request, 'يجب أن يكون الملف المرفق من نوع PDF')
                
                # Handle module notes if provided
                note_key = f'module_{module["id"]}_note'
                if note_key in request.POST:
                    note_content = request.POST[note_key]
                    if note_content.strip():
                        new_module.note = note_content
                        new_module.save()
                
                # Process quizzes with proper validation
                if module.get('has_quiz'):
                    quiz_data = module.get('quiz', {})
                    if not quiz_data:
                        # If quiz data is missing but has_quiz is true, create an empty quiz structure
                        quiz_data = {
                            'title': f'اختبار {new_module.name}',
                            'description': '',
                            'time_limit': 30,
                            'questions': []
                        }
                    
                    # Create the quiz
                    quiz = Quiz.objects.create(
                        module=new_module,
                        title=quiz_data.get('title', f'اختبار {new_module.name}'),
                        description=quiz_data.get('description', ''),
                        time_limit=quiz_data.get('time_limit', 30),
                        pass_mark=quiz_data.get('pass_mark', 50)
                    )
                    
                    # Process questions
                    questions = quiz_data.get('questions', [])
                    
                    # Check if we have questions from the form
                    question_texts = request.POST.getlist(f'module_{module["id"]}_question_text[]', [])
                    question_types = request.POST.getlist(f'module_{module["id"]}_question_type[]', [])
                    
                    # If we have form data for questions, use that instead
                    if question_texts:
                        for i, q_text in enumerate(question_texts):
                            if q_text.strip():
                                q_type = question_types[i] if i < len(question_types) else 'mcq'
                                
                                # Map frontend question types to backend types
                                question_type_map = {
                                    'mcq': 'multiple_choice',
                                    'true_false': 'true_false',
                                    'short_answer': 'short_answer'
                                }
                                
                                # Create the question
                                question = Question.objects.create(
                                    quiz=quiz,
                                    text=q_text,
                                    question_type=question_type_map.get(q_type, 'multiple_choice')
                                )
                                
                                # Get answers for this question (new JSON format)
                                answer_key = f'module_{module["id"]}_question_{i}_answers'
                                if answer_key in request.POST:
                                    try:
                                        answers_data = json.loads(request.POST[answer_key])
                                        answer_texts = answers_data.get('texts', [])
                                        correct_indices = answers_data.get('correct_indices', [])
                                        
                                        # Create answers
                                        for j, a_text in enumerate(answer_texts):
                                            if a_text.strip():
                                                Answer.objects.create(
                                                    question=question,
                                                    text=a_text,
                                                    is_correct=j in correct_indices
                                                )
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Error decoding answers JSON: {e}")
                                        messages.error(request, 'حدث خطأ في معالجة إجابات الأسئلة')
                                else:
                                    # Fallback to old format if new format not available
                                    answer_texts = request.POST.getlist(f'module_{module["id"]}_question_{i}_answer_text[]', [])
                                    correct_answers = request.POST.getlist(f'module_{module["id"]}_question_{i}_correct_answer[]', [])
                                    
                                    for j, a_text in enumerate(answer_texts):
                                        if a_text.strip():
                                            is_correct = str(j) in correct_answers
                                            Answer.objects.create(
                                                question=question,
                                                text=a_text,
                                                is_correct=is_correct
                                            )
                    else:
                        # Use the JSON data if available
                        for q_data in questions:
                            if q_data.get('text'):
                                question = Question.objects.create(
                                    quiz=quiz,
                                    text=q_data.get('text'),
                                    question_type=q_data.get('question_type', 'multiple_choice')
                                )
                                
                                # Process answers
                                answers = q_data.get('answers', [])
                                has_correct_answer = False
                                
                                for a_data in answers:
                                    if a_data.get('text'):
                                        answer = Answer.objects.create(
                                            question=question,
                                            text=a_data.get('text'),
                                            is_correct=a_data.get('is_correct', False)
                                        )
                                        
                                        if answer.is_correct:
                                            has_correct_answer = True
                                
                                # If no correct answer was marked, mark the first one as correct
                                if not has_correct_answer and answers:
                                    first_answer = Answer.objects.filter(question=question).first()
                                    if first_answer:
                                        first_answer.is_correct = True
                                        first_answer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء الدورة بنجاح',
                'redirect_url': reverse('course_detail', args=[course.id])
            })
            
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            messages.error(request, f'حدث خطأ أثناء إنشاء الدورة: {e}')
            return JsonResponse({
                'success': False,
                'message': f'حدث خطأ أثناء إنشاء الدورة: {e}'
            })
    
    # GET request - render form
    categories = Category.objects.all()
    
    # Get user profile and teacher data
    profile = None
    teacher = None
    
    if request.user.is_authenticated:
        try:
            # Get the user's profile
            profile = request.user.profile
            
            # If user is a teacher, get the teacher object
            if hasattr(profile, 'teacher'):
                teacher = profile.teacher
            # If user is a student, get the student object
            elif hasattr(profile, 'student'):
                profile = profile.student
                
        except Exception as e:
            print(f"Error getting user profile: {e}")
    
    return render(request, 'website/courses/create_course.html', {
        'categories': categories,
        'profile': profile,
        'teacher': teacher,
        'student': profile if hasattr(profile, 'student') else None
    })

@login_required
def update_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to edit this course.'))
        return redirect('course')
    
    if request.method == 'POST':
        try:
            # Get basic course data
            name = request.POST.get('name')
            description = request.POST.get('description')
            small_description = request.POST.get('small_description')
            price = request.POST.get('price', 0)
            category_id = request.POST.get('category')
            level = request.POST.get('level', 'beginner')
            
            # Validate required fields
            if not all([name, description, small_description, category_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'الرجاء ملء جميع الحقول المطلوبة'
                })
            
            # Get category
            category = get_object_or_404(Category, id=category_id)
            
            # Update course basic info
            course.name = name
            course.description = description
            course.small_description = small_description
            course.price = price
            course.category = category
            course.level = level
            
            # Handle course image if provided
            if 'course_image' in request.FILES:
                course.image = request.FILES['course_image']
            
            course.save()
            
            # Process modules from JSON data
            module_data = json.loads(request.POST.get('modules', '[]'))
            logger.info(f"Processing {len(module_data)} modules for course {course.id}")
            
            # Track existing modules to identify which ones to delete
            existing_module_ids = set(Module.objects.filter(course=course).values_list('id', flat=True))
            updated_module_ids = set()
            
            for module in module_data:
                module_id = module.get('id')
                is_existing = module.get('is_existing', False)
                
                logger.info(f"Processing module ID: {module_id}, is_existing: {is_existing}")
                
                # Check if this is an existing module or a new one
                if is_existing and module_id and module_id.isdigit() and Module.objects.filter(id=module_id, course=course).exists():
                    # Update existing module
                    existing_module = Module.objects.get(id=module_id)
                    existing_module.name = module.get('name')
                    existing_module.description = module.get('description', '')
                    existing_module.number = module.get('number')
                    existing_module.save()
                    
                    updated_module_ids.add(int(module_id))
                    logger.info(f"Updated existing module {module_id}")
                    
                    # Handle video update if provided
                    video_keys = [
                        f'module_videos_existing_{module_id}',
                        f'module_video_existing_{module_id}',
                        f'module_{module_id}_video'
                    ]
                    for video_key in video_keys:
                        if video_key in request.FILES:
                            video_file = request.FILES[video_key]
                            existing_module.video = video_file
                            existing_module.save()
                            logger.info(f"Updated video for module {module_id}")
                            break
                    
                    # Handle PDF update if provided
                    pdf_keys = [
                        f'module_pdf_existing_{module_id}',
                        f'module_{module_id}_pdf'
                    ]
                    for pdf_key in pdf_keys:
                        if pdf_key in request.FILES:
                            pdf_file = request.FILES[pdf_key]
                            existing_module.pdf = pdf_file
                            existing_module.save()
                            logger.info(f"Updated PDF for module {module_id}")
                            break
                    
                    # Handle quiz update with questions/answers from JSON
                    if module.get('has_quiz'):
                        quiz_data = module.get('quiz', {})
                        quiz, _ = Quiz.objects.get_or_create(
                            module=existing_module,
                            defaults={
                                'title': quiz_data.get('title', f'اختبار {existing_module.name}'),
                                'description': quiz_data.get('description', ''),
                                'time_limit': quiz_data.get('time_limit', 30),
                                'pass_mark': quiz_data.get('pass_mark', 50)
                            }
                        )
                        # Update quiz meta
                        quiz.title = quiz_data.get('title', quiz.title)
                        quiz.description = quiz_data.get('description', quiz.description)
                        quiz.time_limit = quiz_data.get('time_limit', quiz.time_limit)
                        quiz.pass_mark = quiz_data.get('pass_mark', quiz.pass_mark)
                        quiz.save()
                        
                        # Rebuild questions
                        Question.objects.filter(quiz=quiz).delete()
                        for q in quiz_data.get('questions', []):
                            q_type_map = {
                                'multiple_choice': 'multiple_choice',
                                'true_false': 'true_false',
                                'short_answer': 'short_answer'
                            }
                            question_obj = Question.objects.create(
                                quiz=quiz,
                                text=q.get('text',''),
                                question_type=q_type_map.get(q.get('type','multiple_choice'),'multiple_choice')
                            )
                            for ans in q.get('answers', []):
                                Answer.objects.create(
                                    question=question_obj,
                                    text=ans.get('text',''),
                                    is_correct=ans.get('is_correct', False)
                                )
                        logger.info(f"Updated quiz for module {module_id} with {len(quiz_data.get('questions', []))} questions")
                    else:
                        Quiz.objects.filter(module=existing_module).delete()
                    
                else:
                    # Create new module
                    logger.info(f"Creating new module with ID: {module_id}")
                    
                    new_module = Module.objects.create(
                        course=course,
                        name=module.get('name'),
                        description=module.get('description', ''),
                        number=module.get('number', 1)
                    )
                    
                    logger.info(f"Created new module {new_module.id} for course {course.id}")
                    
                    # Save module video with proper file handling
                    video_keys = [
                        f'module_video_new_{module_id}',
                        f'module_{module_id}_video'
                    ]
                    for video_key in video_keys:
                        if video_key in request.FILES:
                            video_file = request.FILES[video_key]
                            # Ensure the file is actually a video
                            if video_file.content_type and (video_file.content_type.startswith('video/') or 
                                any(video_file.name.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv'])):
                                new_module.video = video_file
                                new_module.save()
                                logger.info(f"Added video to new module {new_module.id}")
                            break
                    
                    # Handle PDF files
                    pdf_keys = [
                        f'module_pdf_new_{module_id}',
                        f'module_{module_id}_pdf'
                    ]
                    for pdf_key in pdf_keys:
                        if pdf_key in request.FILES:
                            pdf_file = request.FILES[pdf_key]
                            if pdf_file.content_type == 'application/pdf' or pdf_file.name.lower().endswith('.pdf'):
                                new_module.pdf = pdf_file
                                new_module.save()
                                logger.info(f"Added PDF to new module {new_module.id}")
                            break
                    
                    # Handle notes
                    note_keys = [
                        f'module_notes_new_{module_id}',
                        f'module_{module_id}_notes'
                    ]
                    for note_key in note_keys:
                        if note_key in request.POST:
                            note_content = request.POST.get(note_key)
                            if note_content and note_content.strip():
                                # Add note content to module description
                                if new_module.description:
                                    new_module.description += f"\n\nملاحظات:\n{note_content}"
                                else:
                                    new_module.description = f"ملاحظات:\n{note_content}"
                                new_module.save()
                            break
                    
                    # Handle quiz if enabled
                    if module.get('has_quiz'):
                        quiz_data = module.get('quiz', {})
                        
                        # Create quiz
                        quiz = Quiz.objects.create(
                            module=new_module,
                            title=quiz_data.get('title', f'اختبار {new_module.name}'),
                            description=quiz_data.get('description', ''),
                            time_limit=quiz_data.get('time_limit', 30),
                            pass_mark=quiz_data.get('pass_mark', 50)
                        )
                        
                        # Process questions from JSON data
                        questions = quiz_data.get('questions', [])
                        for q in questions:
                            if q.get('text'):
                                q_type_map = {
                                    'multiple_choice': 'multiple_choice',
                                    'true_false': 'true_false',
                                    'short_answer': 'short_answer'
                                }
                                
                                question_obj = Question.objects.create(
                                    quiz=quiz,
                                    text=q.get('text'),
                                    question_type=q_type_map.get(q.get('type', 'multiple_choice'), 'multiple_choice')
                                )
                                
                                # Process answers
                                for ans in q.get('answers', []):
                                    if ans.get('text'):
                                        Answer.objects.create(
                                            question=question_obj,
                                            text=ans.get('text'),
                                            is_correct=ans.get('is_correct', False)
                                        )
                        
                        logger.info(f"Created quiz for new module {new_module.id} with {len(questions)} questions")
            
            # Delete modules that were not updated or created (and are marked for deletion)
            for module_id in existing_module_ids:
                delete_key = f'delete_module_{module_id}'
                if request.POST.get(delete_key) == '1':
                    try:
                        module_to_delete = Module.objects.get(id=module_id, course=course)
                        module_to_delete.delete()
                        logger.info(f"Deleted module {module_id}")
                    except Module.DoesNotExist:
                        pass
            
            # Process tags
            tags_string = request.POST.get('tags', '')
            if tags_string:
                tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                course.tags.clear()
                for tag in tags:
                    tag_obj, created = Tags.objects.get_or_create(name=tag)
                    course.tags.add(tag_obj)
            
            # Final validation and save
            course.save()
            
            # Log successful update
            logger.info(f"Successfully updated course {course.id} with {len(module_data)} modules")
            
            # Return success response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'تم تحديث الدورة بنجاح',
                    'redirect_url': reverse('course_detail', args=[course.id])
                })
            else:
                messages.success(request, 'تم تحديث الدورة بنجاح')
                return redirect('course_detail', course_id=course.id)
            
        except Exception as e:
            print(f"Error updating course: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    # GET request - display the update form
    categories = Category.objects.all()
    
    # Get user profile and teacher data
    profile = None
    teacher = None
    
    if request.user.is_authenticated:
        try:
            # Get the user's profile
            profile = request.user.profile
            
            # If user is a teacher, get the teacher object
            if hasattr(profile, 'teacher'):
                teacher = profile.teacher
            # If user is a student, get the student object
            elif hasattr(profile, 'student'):
                profile = profile.student
                
        except Exception as e:
            print(f"Error getting user profile: {e}")
    # Prepare tags string
    tags_string = ', '.join([tag.name for tag in course.tags.all()])
    
    context = {
        'course': course,
        'categories': categories,
        'tags_string': tags_string,
        'profile': profile,
        'teacher': teacher,
       'student': profile if hasattr(profile,'student') else None
    }
    return render(request, 'website/courses/update_course.html', context)

@login_required
def delete_course(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is the course teacher or admin
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
        is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
        
        if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
            messages.error(request, _('You do not have permission to delete this course.'))
            return redirect('course')
        
        course.delete()
        messages.success(request, _('Course deleted successfully.'))
    
    return redirect('course')

# Module management views
@login_required
def create_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to add modules to this course.'))
        return redirect('course')
    
    if request.method == 'POST':
        # Process module creation form
        name = request.POST.get('name')
        description = request.POST.get('description')
        order = request.POST.get('order')
        
        module = Module.objects.create(
            course=course,
            name=name,
            description=description,
            order=order
        )
        
        messages.success(request, _('Module created successfully.'))
        return redirect('course_modules', course_id=course_id)
    else:
        # Display module creation form
        return render(request, 'website/create_module.html', {'course': course})

@login_required
def update_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'  
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to edit this module.'))
        return redirect('course')
    
    if request.method == 'POST':
        # Process module update form
        module.name = request.POST.get('name')
        module.description = request.POST.get('description')
        module.order = request.POST.get('order')
        module.save()
        
        messages.success(request, _('Module updated successfully.'))
        return redirect('course_modules', course_id=course_id)
    else:
        # Display module update form
        return render(request, 'website/update_module.html', {'course': course, 'module': module})

@login_required
def delete_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to delete this module.'))
        return redirect('course')
    
    module.delete()
    messages.success(request, _('Module deleted successfully.'))
    return redirect('course_modules', course_id=course_id)

@login_required
def course_modules(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course).order_by('number')
    
    return render(request, 'website/course_modules.html', {'course': course, 'modules': modules})

# Video and content viewing
@login_required
def courseviewpagevideo(request, course_id, video_id):
    course = get_object_or_404(Course, id=course_id)
    video = get_object_or_404(Video, id=video_id, module__course=course)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, _('You are not enrolled in this course.'))
        return redirect('course_detail', course_id=course_id)
    
    # Get all modules for this course
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Mark video as watched
    video_progress, created = VideoProgress.objects.get_or_create(
        student=request.user,
        video=video,
        defaults={'watched': True}
    )
    
    if not created and not video_progress.watched:
        video_progress.watched = True
        video_progress.save()
    
    # Also mark in ContentProgress for new system
    mark_content_completed(request.user, course, 'video', video.id)
    
    # Update enrollment progress
    update_enrollment_progress(enrollment)
    
    # Get completed content IDs for progress tracking
    completed_videos = get_completed_content_ids(request.user, course, 'video')
    completed_notes = get_completed_content_ids(request.user, course, 'note')
    completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
    completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
    
    context = {
        'course': course,
        'modules': modules,
        'video': video,
        'enrollment': enrollment,
        'completed_videos': completed_videos,
        'completed_notes': completed_notes,
        'completed_assignments': completed_assignments,
        'completed_quizzes': completed_quizzes,
    }
    
    return render(request, 'website/courses/courseviewpage.html', context)

@login_required
def courseviewpagenote(request, course_id, note_id):
    course = get_object_or_404(Course, id=course_id)
    note = get_object_or_404(Notes, id=note_id, module__course=course)
    
    # Check if user is enrolled
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
    except Enrollment.DoesNotExist:
        messages.error(request, _('You are not enrolled in this course.'))
        return redirect('course_detail', course_id=course_id)
    
    # Get all modules for this course
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Mark note as viewed in ContentProgress
    mark_content_completed(request.user, course, 'note', note.id)
    
    # Update enrollment progress
    update_enrollment_progress(enrollment)
    
    # Get completed content IDs for progress tracking
    completed_videos = get_completed_content_ids(request.user, course, 'video')
    completed_notes = get_completed_content_ids(request.user, course, 'note')
    completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
    completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
    
    context = {
        'course': course,
        'modules': modules,
        'note': note,
        'enrollment': enrollment,
        'completed_videos': completed_videos,
        'completed_notes': completed_notes,
        'completed_assignments': completed_assignments,
        'completed_quizzes': completed_quizzes,
    }
    
    return render(request, 'website/courses/courseviewpage.html', context)

# Progress tracking
@login_required
@require_POST
def mark_video_watched(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    course = video.module.course
    
    # Mark video as watched
    video_progress, created = VideoProgress.objects.get_or_create(
        student=request.user,
        video=video,
        defaults={'watched': True}
    )
    
    if not created and not video_progress.watched:
        video_progress.watched = True
        video_progress.save()
    
    # Also mark in ContentProgress for new system
    progress = mark_content_completed(request.user, course, 'video', video_id)
    
    return JsonResponse({
        'status': 'success',
        'message': _('Video marked as watched'),
        'progress': progress
    })

@login_required
@require_POST  
def mark_content_viewed(request, content_type, content_id):
    """Enhanced content tracking for all module content types"""
    try:
        course = None
        
        # Handle different content types
        if content_type == 'module_video':
            # Module video - get course from module
            module = get_object_or_404(Module, id=content_id)
            course = module.course
            # Mark as video content for tracking
            track_type = 'video'
            track_id = f'module_video_{content_id}'
            
        elif content_type == 'module_pdf':
            # Module PDF - get course from module  
            module = get_object_or_404(Module, id=content_id)
            course = module.course
            track_type = 'pdf'
            track_id = f'module_pdf_{content_id}'
            
        elif content_type == 'module_note':
            # Module notes - get course from module
            module = get_object_or_404(Module, id=content_id)
            course = module.course
            track_type = 'note'
            track_id = f'module_note_{content_id}'
            
        elif content_type == 'quiz':
            # Quiz - can be module or course level
            quiz = get_object_or_404(Quiz, id=content_id)
            course = quiz.course
            track_type = 'quiz'
            track_id = content_id
            
        elif content_type == 'assignment':
            # Assignment - can be module or course level
            assignment = get_object_or_404(Assignment, id=content_id)
            course = assignment.course
            track_type = 'assignment' 
            track_id = content_id
            
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid content type: {content_type}'
            }, status=400)
        
        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(course=course, student=request.user)
        except Enrollment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'You are not enrolled in this course'
            }, status=403)
        
        # Mark content as completed
        print(f"[DEBUG] Marking {track_type} {track_id} as completed for {request.user.username}")
        progress_percentage = mark_content_completed(request.user, course, track_type, track_id)
        
        # Update enrollment progress
        enrollment.progress = progress_percentage
        enrollment.save(update_fields=['progress'])
        
        print(f"[DEBUG] Updated progress to {progress_percentage}% for {request.user.username}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Content marked as viewed successfully',
            'progress': progress_percentage,
            'content_type': content_type,
            'content_id': content_id
        })
        
    except Exception as e:
        print(f"[ERROR] Error in mark_content_viewed: {e}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)

@login_required
@require_POST
def mark_assignment_completed(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Mark assignment as completed
    progress = mark_content_completed(request.user, course, 'assignment', assignment_id)
    
    return JsonResponse({
        'status': 'success',
        'message': _('Assignment marked as completed'),
        'progress': progress
    })

@login_required
@require_POST
def complete_course(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is enrolled
        enrollment = get_object_or_404(Enrollment, course=course, student=request.user)
        
        # Check if user has sufficient progress (at least 80%)
        if enrollment.progress >= 80:
            # Force completion
            enrollment.status = 'completed'
            enrollment.progress = 100.0
            enrollment.last_accessed = timezone.now()
            enrollment.save()
            
            # Update progress using utils function
            final_progress = update_enrollment_progress(enrollment)
            
            return JsonResponse({
                'status': 'success',
                'message': 'تم إنهاء الدورة بنجاح',
                'progress': final_progress,
                'completion_date': enrollment.last_accessed.isoformat() if enrollment.last_accessed else None
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'يجب إكمال على الأقل 80% من الدورة للإنهاء. التقدم الحالي: {enrollment.progress:.1f}%'
            }, status=400)
            
    except Enrollment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'غير مسجل في هذه الدورة'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)

@login_required
@require_POST
def recalculate_progress(request, course_id):
    """Recalculate course progress for the enrolled user"""
    try:
        course = get_object_or_404(Course, id=course_id)
        enrollment = get_object_or_404(Enrollment, course=course, student=request.user)
        
        # Recalculate the progress
        new_progress = update_enrollment_progress(enrollment)
        
        logger.info(f"Progress recalculated for user {request.user.username} in course {course.name}: {new_progress}%")
        
        return JsonResponse({
            'status': 'success',
            'progress': new_progress,
            'message': f'تم إعادة حساب التقدم: {new_progress:.1f}%'
        })
        
    except Exception as e:
        logger.error(f"Error recalculating progress: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'حدث خطأ في إعادة حساب التقدم'
        })

@login_required
def check_final_exam_completion(request, course_id):
    """Check if user passed any final exam for the course"""
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # البحث عن جميع الامتحانات النهائية للكورس
        final_exams = Exam.objects.filter(
            course=course,
            is_final=True,
            is_active=True
        )
        
        # التحقق من محاولات المستخدم في الامتحانات النهائية
        passed_final_exams = []
        for exam in final_exams:
            successful_attempt = UserExamAttempt.objects.filter(
                user=request.user,
                exam=exam,
                passed=True
            ).first()
            
            if successful_attempt:
                passed_final_exams.append({
                    'exam_id': exam.id,
                    'exam_title': exam.title,
                    'score': successful_attempt.score,
                    'attempt_number': successful_attempt.attempt_number,
                    'completion_date': successful_attempt.end_time
                })
        
        # إذا نجح في أي امتحان نهائي، الكورس مكتمل
        course_completed = len(passed_final_exams) > 0
        
        logger.info(f"Final exam check for user {request.user.username} in course {course.name}: {'PASSED' if course_completed else 'NOT PASSED'}")
        
        return JsonResponse({
            'status': 'success',
            'course_completed': course_completed,
            'passed_final_exams': passed_final_exams,
            'total_final_exams': final_exams.count(),
            'progress': 100.0 if course_completed else None,
            'message': 'تم التحقق من حالة الامتحان النهائي'
        })
        
    except Exception as e:
        logger.error(f"Error checking final exam completion: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'حدث خطأ في التحقق من الامتحان النهائي'
        })

@login_required
@require_POST
def recalculate_all_progress(request):
    """Recalculate progress for all user's enrolled courses"""
    try:
        enrollments = Enrollment.objects.filter(student=request.user)
        updated_courses = []
        total_progress = 0
        
        for enrollment in enrollments:
            # استخدام دالة update_enrollment_progress المحدثة
            new_progress = update_enrollment_progress(enrollment)
            
            updated_courses.append({
                'course_id': enrollment.course.id,
                'course_name': enrollment.course.name,
                'progress': new_progress
            })
            
            total_progress += new_progress
        
        # حساب متوسط التقدم
        average_progress = total_progress / len(enrollments) if enrollments else 0
        
        logger.info(f"Recalculated progress for {len(enrollments)} courses for user {request.user.username}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'تم إعادة حساب التقدم لـ {len(enrollments)} دورة',
            'updated_courses': updated_courses,
            'average_progress': average_progress,
            'total_courses': len(enrollments)
        })
        
    except Exception as e:
        logger.error(f"Error recalculating all progress: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'حدث خطأ في إعادة حساب التقدم'
        })

# Quiz management
@login_required
def quiz_list(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    quizzes = Quiz.objects.filter(video=video)
    return render(request, 'website/quiz_list.html', {'video': video, 'quizzes': quizzes})

@login_required
def view_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    return render(request, 'website/quiz_detail.html', {'quiz': quiz})

@login_required
def create_quiz(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    course = video.module.course
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to create quizzes for this course.'))
        return redirect('course')
    
    if request.method == 'POST':
        # Process quiz creation form
        title = request.POST.get('title')
        description = request.POST.get('description')
        passing_score = request.POST.get('passing_score', 70)
        
        quiz = Quiz.objects.create(
            title=title,
            description=description,
            video=video,
            course=course,
            passing_score=passing_score
        )
        
        # Process questions
        question_count = int(request.POST.get('question_count', 0))
        for i in range(1, question_count + 1):
            question_text = request.POST.get(f'question_{i}')
            if question_text:
                question = Question.objects.create(
                    quiz=quiz,
                    text=question_text
                )
                
                # Process answers for this question
                for j in range(1, 5):  # Assuming 4 possible answers per question
                    answer_text = request.POST.get(f'question_{i}_answer_{j}')
                    is_correct = request.POST.get(f'question_{i}_correct') == str(j)
                    
                    if answer_text:
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=is_correct
                        )
        
        messages.success(request, _('Quiz created successfully.'))
        return redirect('quiz_list', video_id=video_id)
    else:
        # Display quiz creation form
        return render(request, 'website/create_quiz.html', {'video': video})

@login_required
def update_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user == course.teacher.profile.user) and not (is_admin or request.user.is_superuser):
        messages.error(request, _('You do not have permission to edit this quiz.'))
        return redirect('course')
    
    if request.method == 'POST':
        # Process quiz update form
        quiz.title = request.POST.get('title')
        quiz.description = request.POST.get('description')
        quiz.passing_score = request.POST.get('passing_score', 70)
        quiz.save()
        
        # Process existing questions
        existing_questions = request.POST.getlist('existing_question_id[]')
        for question_id in existing_questions:
            question = get_object_or_404(Question, id=question_id)
            question.text = request.POST.get(f'existing_question_{question_id}')
            question.save()
            
            # Process answers for this question
            existing_answers = request.POST.getlist(f'existing_answer_id_{question_id}[]')
            for answer_id in existing_answers:
                answer = get_object_or_404(Answer, id=answer_id)
                answer.text = request.POST.get(f'existing_answer_{answer_id}')
                answer.is_correct = request.POST.get(f'existing_correct_{question_id}') == str(answer_id)
                answer.save()
        
        # Process new questions
        new_question_count = int(request.POST.get('new_question_count', 0))
        for i in range(1, new_question_count + 1):
            question_text = request.POST.get(f'new_question_{i}')
            if question_text:
                question = Question.objects.create(
                    quiz=quiz,
                    text=question_text
                )
                
                # Process answers for this question
                for j in range(1, 5):  # Assuming 4 possible answers per question
                    answer_text = request.POST.get(f'new_question_{i}_answer_{j}')
                    is_correct = request.POST.get(f'new_question_{i}_correct') == str(j)
                    
                    if answer_text:
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=is_correct
                        )
        
        messages.success(request, _('Quiz updated successfully.'))
        return redirect('quiz_list', video_id=quiz.video.id)
    else:
        # Display quiz update form
        return render(request, 'website/update_quiz.html', {'quiz': quiz})

@login_required
@require_POST
def submit_quiz(request):
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            quiz_id = data.get('quiz_id')
            answers = data.get('answers', {})
        else:
            quiz_id = request.POST.get('quiz_id')
            answers = {}
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = key.replace('question_', '')
                    answers[question_id] = value
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Get course - check if quiz has course directly or via module
        course = quiz.course
        if not course and quiz.module:
            course = quiz.module.course
        
        if not course:
            raise ValueError("Quiz is not associated with any course")
        
        # Calculate score
        total_questions = quiz.questions.count()
        if total_questions == 0:
            raise ValueError("Quiz has no questions")
        
        correct_answers = 0
        
        # Create quiz attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            attempt_number=QuizAttempt.objects.filter(user=request.user, quiz=quiz).count() + 1
        )
        
        for question_id, answer_id in answers.items():
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                selected_answer = Answer.objects.get(id=answer_id, question=question)
                
                is_correct = selected_answer.is_correct
                if is_correct:
                    correct_answers += 1
                
                # Record user answer
                QuizUserAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    points_earned=question.points if is_correct else 0
                )
            except (Question.DoesNotExist, Answer.DoesNotExist):
                pass
        
        if total_questions > 0:
            score = (correct_answers / total_questions) * 100
        else:
            score = 0
        
        # Check if passed
        passed = score >= quiz.pass_mark
        
        # Update attempt with final score and status
        attempt.score = score
        attempt.passed = passed
        attempt.end_time = timezone.now()
        attempt.save()
        
        # If passed, mark as completed in ContentProgress
        if passed:
            mark_content_completed(request.user, course, 'quiz', quiz_id)
        
        # Update enrollment progress
        try:
            enrollment = Enrollment.objects.get(course=course, student=request.user)
            progress = update_enrollment_progress(enrollment)
        except Enrollment.DoesNotExist:
            progress = 0
        
        # Handle different request types (AJAX vs form)
        if request.content_type == 'application/json':
            return JsonResponse({
                'status': 'success',
                'score': score,
                'passed': passed,
                'passing_score': quiz.pass_mark,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'progress': progress
            })
        else:
            # Success message based on result
            if passed:
                messages.success(request, f'🎉 مبروك! نجحت في الاختبار بدرجة {score:.1f}%')
            else:
                messages.warning(request, f'⚠️ لم تحقق الدرجة المطلوبة. حصلت على {score:.1f}% والمطلوب {quiz.pass_mark}%')
            
            # Find next content to redirect to
            next_content_url = find_next_content_url(course, 'quiz', quiz_id, request.user)
            if next_content_url:
                return redirect(next_content_url)
            else:
                # If no next content, go back to course with current content highlighted
                return redirect(f'/courseviewpage/{course.id}/?content_type=quiz&content_id={quiz_id}')
            
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        else:
            messages.error(request, f'حدث خطأ أثناء تسليم الاختبار: {str(e)}')
            # Try to get course safely
            try:
                if 'quiz' in locals():
                    course = quiz.course or (quiz.module.course if quiz.module else None)
                    if course:
                        return redirect('courseviewpage', course_id=course.id)
                # If we can't find a course, redirect to dashboard
                return redirect('dashboard')
            except:
                return redirect('dashboard')

@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    video_id = quiz.video.id
    course = quiz.course
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
        messages.error(request, _('You do not have permission to delete this quiz.'))
        return redirect('course')
    
    quiz.delete()
    messages.success(request, _('Quiz deleted successfully.'))
    return redirect('quiz_list', video_id=video_id)

@student_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(course=course, student=request.user).exists():
        messages.info(request, _('You are already enrolled in this course.'))
        return redirect('courseviewpage', course_id=course_id)
    
    # Check if course is free or if user has the course in their cart
    if course.price == 0 or CartItem.objects.filter(cart__user=request.user, course=course).exists():
        # Create enrollment
        Enrollment.objects.create(
            course=course,
            student=request.user
        )
        # Remove from cart if it was there
        CartItem.objects.filter(cart__user=request.user, course=course).delete()
        messages.success(request, _('Successfully enrolled in the course.'))
        return redirect('courseviewpage', course_id=course_id)
    else:
        messages.error(request, _('You need to add this course to your cart and complete the purchase before enrolling.'))
        return redirect('view_cart')
        return redirect('course_detail', course_id=course_id)


# File management
@login_required
@require_POST
def delete_pdf(request, course_id, pdf_type):
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is the course teacher
        if request.user != course.teacher.profile.user:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to delete files from this course.'
            }, status=403)
        
        if pdf_type == 'syllabus_pdf':
            if course.syllabus_pdf:
                course.syllabus_pdf.delete()
                course.syllabus_pdf = None
                course.save()
        elif pdf_type == 'materials_pdf':
            if course.materials_pdf:
                course.materials_pdf.delete()
                course.materials_pdf = None
                course.save()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid PDF type'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'File deleted successfully.'
        })
        
    except Exception as e:
        logger.error(f"Error deleting PDF: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def delete_module_pdf(request, module_id, pdf_type):
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
        messages.error(request, _('You do not have permission to delete files from this module.'))
        return redirect('course')
    
    if pdf_type == 'module_pdf':
        if module.module_pdf:
            module.module_pdf.delete()
            module.module_pdf = None
    elif pdf_type == 'additional_materials':
        if module.additional_materials:
            module.additional_materials.delete()
            module.additional_materials = None
    
    module.save()
    messages.success(request, _('File deleted successfully.'))
    return redirect('update_module', course_id=course.id, module_id=module.id)

# Cart functionality

@student_required
def add_to_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(course=course, student=request.user).exists():
        messages.info(request, _('You are already enrolled in this course.'))
        return redirect('courseviewpage', course_id=course_id)
    
    # Add to cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, course=course)
    
    if created:
        messages.success(request, _('Course added to cart.'))
    else:
        messages.info(request, _('Course is already in your cart.'))
    
    return redirect('view_cart')

@student_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.course.price for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total_price = 0
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    
    return render(request, 'website/cart.html', context)

@student_required
def remove_from_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, course=course)
        cart_item.delete()
        messages.success(request, _('Course removed from cart.'))
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        messages.error(request, _('Course not found in cart.'))
    
    return redirect('view_cart')

@student_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            messages.error(request, _('Your cart is empty.'))
            return redirect('view_cart')
        
        # Process payment (simplified for now)
        for item in cart_items:
            # Create enrollment for purchased course
            enrollment, created = Enrollment.objects.get_or_create(
                course=item.course,
                student=request.user,
                defaults={
                    'enrollment_date': timezone.now(),
                    'status': 'active',
                    'progress': 0
                }
            )
        
        # Clear the cart after successful checkout
        cart_items.delete()
        
        messages.success(request, _('Purchase completed successfully. You are now enrolled in the courses.'))
        return redirect('dashboard')
    
    except Cart.DoesNotExist:
        messages.error(request, _('Your cart is empty.'))
        return redirect('view_cart')

# Comments
@login_required
@require_POST
def add_comment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    comment_text = request.POST.get('comment_text')
    
    if comment_text:
        Comment.objects.create(
            user=request.user,
            course=course,
            description=comment_text
        )
        messages.success(request, _('Comment added successfully'))
        return redirect('courseviewpage', course_id=course_id)
    
    messages.error(request, _('Comment text is required'))
    return redirect('courseviewpage', course_id=course_id)

# Ratings
@student_required
@require_POST
def add_rating(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    rating_value = request.POST.get('rating')
    review_text = request.POST.get('review', '')
    
    # Validate rating
    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            raise ValueError('Rating must be between 1 and 5')
    except (ValueError, TypeError):
        messages.error(request, _('Invalid rating value. Please provide a rating between 1 and 5.'))
        return redirect('courseviewpage', course_id=course_id)
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(course=course, student=request.user).exists():
        messages.error(request, _('You must be enrolled in the course to rate it.'))
        return redirect('courseviewpage', course_id=course_id)
    
    # Update or create rating
    rating, created = Rating.objects.update_or_create(
        user=request.user,
        course=course,
        defaults={
            'rating': rating_value,
            'review': review_text
        }
    )
    
    # Update course average rating
    course_ratings = Rating.objects.filter(course=course)
    if course_ratings.exists():
        avg_rating = course_ratings.aggregate(Avg('rating'))['rating__avg']
        course.rating = round(avg_rating, 1)
        course.save()
    
    if created:
        messages.success(request, _('Thank you for rating this course!'))
    else:
        messages.success(request, _('Your rating has been updated.'))
    
    return redirect('courseviewpage', course_id=course_id)

# Certificate generation
@login_required
def generate_certificate(request, course_id):
    """إنتاج شهادة إكمال الدورة للطالب"""
    course = get_object_or_404(Course, id=course_id)
    
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
        
        # التحقق من إكمال الدورة أو النجاح في الامتحان النهائي
        course_completed = False
        completion_reason = ""
        
        # شرط 1: نسبة التقدم 100%
        if enrollment.progress >= 100:
            course_completed = True
            completion_reason = "إكمال جميع عناصر الدورة"
        
        # شرط 2: النجاح في امتحان نهائي (حتى لو التقدم < 100%)
        elif enrollment.progress >= 80:  # حد أدنى 80%
            from .models import Exam, UserExamAttempt
            final_exams = Exam.objects.filter(
                course=course,
                is_final=True,
                is_active=True
            )
            
            for exam in final_exams:
                passed_attempt = UserExamAttempt.objects.filter(
                    user=request.user,
                    exam=exam,
                    passed=True
                ).first()
                
                if passed_attempt:
                    course_completed = True
                    completion_reason = f"النجاح في الامتحان النهائي ({passed_attempt.score:.1f}%)"
                    break
        
        if not course_completed:
            messages.error(request, 'يجب إكمال الدورة أو النجاح في الامتحان النهائي للحصول على الشهادة.')
            return redirect('courseviewpage', course_id=course_id)
        
        # الحصول على القالب المناسب
        template = None
        if hasattr(course, 'teacher') and course.teacher:
            # البحث عن قالب المعلم
            template = CertificateTemplate.objects.filter(
                created_by=course.teacher.profile.user,
                is_active=True
            ).first()
        
        # إذا لم يوجد قالب للمعلم، استخدم القالب الافتراضي
        if not template:
            template = CertificateTemplate.get_default_template()
        
        # إنشاء أو تحديث الشهادة
        certificate, created = Certificate.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'template': template,
                'completion_date': timezone.now(),
                'final_grade': enrollment.progress,
                'completion_percentage': enrollment.progress,
                'course_duration_hours': getattr(course, 'duration_hours', None),
                'issued_by': course.teacher.profile.user if hasattr(course, 'teacher') and course.teacher else None,
                'institution_name': template.institution_name if template else "أكاديمية التعلم الإلكتروني"
            }
        )
        
        # تحديث البيانات إذا كانت الشهادة موجودة مسبقاً
        if not created:
            certificate.final_grade = enrollment.progress
            certificate.completion_percentage = enrollment.progress
            certificate.template = template
            certificate.save()
        
        # إنتاج رمز QR إذا كان مطلوباً
        if certificate.template and certificate.template.include_qr_code:
            certificate.generate_qr_code()
            certificate.save()
        
        logger.info(f"Certificate generated for user {request.user.username} in course {course.name}: {completion_reason}")
        
        # عرض الشهادة
        context = {
            'certificate': certificate,
            'course': course,
            'user': request.user,
            'template': certificate.get_template_or_default(),
            'completion_reason': completion_reason,
            'formatted_certificate_text': certificate.get_template_or_default().format_certificate_text(
                certificate.student_name,
                certificate.course_title,
                certificate.completion_date.strftime('%Y-%m-%d'),
                certificate.get_grade_display() if certificate.template and certificate.template.include_grade else None,
                certificate.get_duration_display() if certificate.template and certificate.template.include_course_duration else None
            ) if certificate.get_template_or_default() else None
        }
        
        return render(request, 'website/certificate.html', context)
    
    except Enrollment.DoesNotExist:
        messages.error(request, 'أنت غير مسجل في هذه الدورة.')
        return redirect('courseviewpage', course_id=course_id)
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        messages.error(request, 'حدث خطأ أثناء إنتاج الشهادة. الرجاء المحاولة مرة أخرى.')
        return redirect('courseviewpage', course_id=course_id)

@login_required
def download_certificate(request, certificate_id):
    """تحميل الشهادة كملف PDF"""
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    
    # التحقق من صلاحية الشهادة
    if not certificate.is_valid():
        messages.error(request, 'هذه الشهادة غير صالحة أو تم إلغاؤها.')
        return redirect('courseviewpage', course_id=certificate.course.id)
    
    try:
        # إذا كان ملف PDF موجود مسبقاً، قم بإرساله
        if certificate.pdf_file and default_storage.exists(certificate.pdf_file.name):
            response = HttpResponse(certificate.pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_id}.pdf"'
            return response
        
        # إنتاج ملف PDF جديد باستخدام القالب
        template = certificate.get_template_or_default()
        
        # إنشاء HTML للشهادة
        from django.template.loader import render_to_string
        from django.conf import settings
        import pdfkit
        
        # تحضير البيانات للقالب
        context = {
            'certificate': certificate,
            'template': template,
            'template_css_vars': template.get_template_css() if template else {},
            'formatted_certificate_text': template.format_certificate_text(
                certificate.student_name,
                certificate.course_title,
                certificate.completion_date.strftime('%Y-%m-%d'),
                certificate.get_grade_display() if template and template.include_grade else None,
                certificate.get_duration_display() if template and template.include_course_duration else None
            ) if template else f"شهادة إتمام دورة {certificate.course_title}",
            'for_pdf': True,  # فلاج للإشارة أن هذا للـ PDF
        }
        
        # إنتاج HTML
        html_content = render_to_string('website/certificate_pdf.html', context)
        
        # إعدادات PDF
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
            'disable-smart-shrinking': None,
        }
        
        try:
            # إنتاج PDF باستخدام wkhtmltopdf
            pdf_content = pdfkit.from_string(html_content, False, options=options)
            
            # حفظ PDF في الملف
            from django.core.files.base import ContentFile
            pdf_filename = f"certificate_{certificate.certificate_id}.pdf"
            certificate.pdf_file.save(pdf_filename, ContentFile(pdf_content), save=True)
            
        except Exception as pdf_error:
            logger.warning(f"wkhtmltopdf not available, using fallback: {pdf_error}")
            
            # Fallback: إنتاج PDF بسيط باستخدام ReportLab
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            buffer = BytesIO()
            
            # إعداد الصفحة
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # الأنماط
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                spaceAfter=30,
                alignment=1,  # مركز
                textColor=HexColor(template.primary_color if template else '#2a5a7c')
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=18,
                spaceAfter=20,
                alignment=1,
                textColor=HexColor(template.secondary_color if template else '#28a745')
            )
            
            text_style = ParagraphStyle(
                'CustomText',
                parent=styles['Normal'],
                fontSize=14,
                spaceAfter=12,
                alignment=1
            )
            
            # محتوى الشهادة
            story = []
            
            # العنوان
            story.append(Paragraph("شهادة إتمام الدورة", title_style))
            story.append(Spacer(1, 20))
            
            # اسم المؤسسة
            story.append(Paragraph(certificate.institution_name, subtitle_style))
            story.append(Spacer(1, 30))
            
            # النص الرئيسي
            if template:
                formatted_text = template.format_certificate_text(
                    certificate.student_name,
                    certificate.course_title,
                    certificate.completion_date.strftime('%Y-%m-%d'),
                    certificate.get_grade_display() if template.include_grade else None,
                    certificate.get_duration_display() if template.include_course_duration else None
                )
            else:
                formatted_text = f"نشهد بأن {certificate.student_name} قد أكمل بنجاح دورة {certificate.course_title}"
            
            story.append(Paragraph(formatted_text, text_style))
            story.append(Spacer(1, 40))
            
            # التوقيع والتاريخ
            story.append(Paragraph(f"التاريخ: {certificate.completion_date.strftime('%Y-%m-%d')}", text_style))
            story.append(Paragraph(f"رقم الشهادة: {certificate.certificate_id}", text_style))
            story.append(Paragraph(f"رمز التحقق: {certificate.verification_code}", text_style))
            
            # إنتاج PDF
            doc.build(story)
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            
            # حفظ PDF
            from django.core.files.base import ContentFile
            pdf_filename = f"certificate_{certificate.certificate_id}.pdf"
            certificate.pdf_file.save(pdf_filename, ContentFile(pdf_content), save=True)
        
        # إرسال الملف
        response = HttpResponse(certificate.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_id}.pdf"'
        
        logger.info(f"Certificate PDF downloaded: {certificate.certificate_id}")
        return response
    
    except Exception as e:
        logger.error(f"Error generating certificate PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'حدث خطأ أثناء إنتاج ملف PDF للشهادة. الرجاء المحاولة مرة أخرى.')
        return redirect('courseviewpage', course_id=certificate.course.id)

# Course statistics and analytics
@login_required
def course_statistics(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
        messages.error(request, _('You do not have permission to view statistics for this course.'))
        return redirect('course')
    
    # Get enrollment stats
    total_enrollments = Enrollment.objects.filter(course=course).count()
    active_enrollments = Enrollment.objects.filter(course=course, status='active').count()
    completed_enrollments = Enrollment.objects.filter(course=course, progress=100).count()
    
    # Get content engagement stats
    video_views = VideoProgress.objects.filter(video__module__course=course).count()
    note_views = NoteProgress.objects.filter(note__module__course=course).count()
    quiz_attempts = UserExamAttempt.objects.filter(exam__course=course).count()
    quiz_passes = UserExamAttempt.objects.filter(exam__course=course, passed=True).count()
    
    # Get average progress
    avg_progress = Enrollment.objects.filter(course=course).aggregate(Avg('progress'))['progress__avg'] or 0
    
    # Get ratings data
    ratings = Rating.objects.filter(course=course)
    rating_counts = {
        1: ratings.filter(rating=1).count(),
        2: ratings.filter(rating=2).count(),
        3: ratings.filter(rating=3).count(),
        4: ratings.filter(rating=4).count(),
        5: ratings.filter(rating=5).count(),
    }
    
    # Get revenue data if applicable
    revenue = CartItem.objects.filter(course=course, purchased=True).count() * course.price
    
    context = {
        'course': course,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'completion_rate': (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0,
        'video_views': video_views,
        'note_views': note_views,
        'quiz_attempts': quiz_attempts,
        'quiz_passes': quiz_passes,
        'quiz_pass_rate': (quiz_passes / quiz_attempts * 100) if quiz_attempts > 0 else 0,
        'avg_progress': avg_progress,
        'rating_counts': rating_counts,
        'revenue': revenue,
    }
    
    return render(request, 'website/course_statistics.html', context)

# Course search and filtering
@login_required
def search_courses(request):
    courses, search_query = searchCourses(request)
    
    # Additional filtering
    category = request.GET.get('category')
    if category:
        courses = courses.filter(category__name=category)
    
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    price = request.GET.get('price')
    if price == 'free':
        courses = courses.filter(price=0)
    elif price == 'paid':
        courses = courses.filter(price__gt=0)
    
    sort = request.GET.get('sort')
    if sort == 'newest':
        courses = courses.order_by('-created_at')
    elif sort == 'oldest':
        courses = courses.order_by('created_at')
    elif sort == 'price_low':
        courses = courses.order_by('price')
    elif sort == 'price_high':
        courses = courses.order_by('-price')
    elif sort == 'rating':
        courses = courses.order_by('-rating')
    
    # Get all categories for filtering
    categories = Category.objects.all()
    
    context = {
        'courses': courses,
        'search_query': search_query,
        'categories': categories,
        'selected_category': category,
        'selected_level': level,
        'selected_price': price,
        'selected_sort': sort,
    }
    
    return render(request, 'website/courses_search.html', context)

# Course recommendations
def course_recommendations(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Get courses in the same category
    same_category = Course.objects.filter(category=course.category).exclude(id=course.id).order_by('-rating')[:3]
    
    # Get courses by the same teacher
    same_teacher = Course.objects.filter(teacher=course.teacher).exclude(id=course.id).order_by('-created_at')[:3]
    
    # Get popular courses (most enrollments)
    popular_courses = Course.objects.annotate(enrollment_count=Count('enrollment')).exclude(id=course.id).order_by('-enrollment_count')[:3]
    
    context = {
        'course': course,
        'same_category': same_category,
        'same_teacher': same_teacher,
        'popular_courses': popular_courses,
    }
    
    return render(request, 'website/course_recommendations.html', context)

# Course wishlist
@login_required
def add_to_wishlist(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already in wishlist
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    if course in wishlist.courses.all():
        messages.info(request, _('Course is already in your wishlist.'))
    else:
        wishlist.courses.add(course)
        messages.success(request, _('Course added to your wishlist.'))
    
    return redirect('coursedetail', course_id=course_id)

@login_required
def remove_from_wishlist(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        if course in wishlist.courses.all():
            wishlist.courses.remove(course)
            messages.success(request, _('Course removed from your wishlist.'))
        else:
            messages.info(request, _('Course is not in your wishlist.'))
    except Wishlist.DoesNotExist:
        messages.info(request, _('You do not have a wishlist.'))
    
    return redirect('view_wishlist')

@login_required
def view_wishlist(request):
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        courses = wishlist.courses.all()
    except Wishlist.DoesNotExist:
        courses = []
    
    context = {
        'courses': courses
    }
    
    return render(request, 'website/wishlist.html', context)

# Discussion system views
@login_required
@require_POST
def add_course_comment(request, course_id):
    """Add a new comment to a course"""
    course = get_object_or_404(Course, id=course_id)
    comment_text = request.POST.get('comment_text', '').strip()
    
    if not comment_text:
        return JsonResponse({
            'success': False,
            'message': 'نص التعليق مطلوب'
        })
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(course=course, student=request.user).exists():
        return JsonResponse({
            'success': False,
            'message': 'يجب أن تكون مسجلاً في الدورة لإضافة تعليق'
        })
    
    try:
        comment = Comment.objects.create(
            user=request.user,
            course=course,
            content=comment_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'تم إضافة التعليق بنجاح',
            'comment_id': comment.id,
            'comment_html': render_comment_html(comment, request.user)
        })
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء إضافة التعليق'
        })


@login_required
@require_POST
def add_comment_reply(request, comment_id):
    """Add a reply to a comment"""
    comment = get_object_or_404(Comment, id=comment_id, is_active=True)
    reply_text = request.POST.get('reply_text', '').strip() or request.POST.get('reply_content', '').strip()
    
    if not reply_text:
        return JsonResponse({
            'success': False,
            'message': 'نص الرد مطلوب'
        })
    
    # Check permissions: Students must be enrolled, Teachers/Admins can reply to any comment on their courses
    user_profile = request.user.profile
    can_reply = False
    
    if user_profile.status == 'Student':
        # Students must be enrolled in the course
        can_reply = Enrollment.objects.filter(course=comment.course, student=request.user).exists()
    elif user_profile.status in ['Teacher', 'Admin']:
        # Teachers/Admins can reply to comments on their courses or any course they teach
        can_reply = (
            Course.objects.filter(teacher__profile__user=request.user, id=comment.course.id).exists() or
            user_profile.status == 'Admin'  # Admins can reply to any comment
        )
    
    if not can_reply:
        return JsonResponse({
            'success': False,
            'message': 'ليس لديك صلاحية للرد على هذا التعليق'
        })
    
    try:
        reply = SubComment.objects.create(
            user=request.user,
            comment=comment,
            content=reply_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'تم إضافة الرد بنجاح',
            'reply_id': reply.id,
            'reply_html': render_discussion_reply_html(reply, request.user)
        })
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء إضافة الرد'
        })


@login_required
@require_POST
def like_comment(request, comment_id):
    """Like or unlike a comment"""
    comment = get_object_or_404(Comment, id=comment_id, is_active=True)
    
    # Check permissions: Students must be enrolled, Teachers/Admins can like comments on their courses
    user_profile = request.user.profile
    can_like = False
    
    if user_profile.status == 'Student':
        # Students must be enrolled in the course
        can_like = Enrollment.objects.filter(course=comment.course, student=request.user).exists()
    elif user_profile.status in ['Teacher', 'Admin']:
        # Teachers/Admins can like comments on their courses or any course they teach
        can_like = (
            Course.objects.filter(teacher__profile__user=request.user, id=comment.course.id).exists() or
            user_profile.status == 'Admin'  # Admins can like any comment
        )
    
    if not can_like:
        return JsonResponse({
            'success': False,
            'message': 'ليس لديك صلاحية للتفاعل مع هذا التعليق'
        })
    
    try:
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )
        
        if created:
            liked = True
            message = 'تم الإعجاب بالتعليق'
        else:
            like.delete()
            liked = False
            message = 'تم إلغاء الإعجاب'
        
        likes_count = comment.likes.count()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'liked': liked,
            'likes_count': likes_count
        })
    except Exception as e:
        logger.error(f"Error liking comment: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ'
        })


@login_required
@require_POST
def like_subcomment(request, subcomment_id):
    """Like or unlike a sub-comment"""
    subcomment = get_object_or_404(SubComment, id=subcomment_id, is_active=True)
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(course=subcomment.comment.course, student=request.user).exists():
        return JsonResponse({
            'success': False,
            'message': 'يجب أن تكون مسجلاً في الدورة'
        })
    
    try:
        like, created = SubCommentLike.objects.get_or_create(
            user=request.user,
            subcomment=subcomment
        )
        
        if created:
            liked = True
            message = 'تم الإعجاب بالرد'
        else:
            like.delete()
            liked = False
            message = 'تم إلغاء الإعجاب'
        
        likes_count = subcomment.likes.count()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'liked': liked,
            'likes_count': likes_count
        })
    except Exception as e:
        logger.error(f"Error liking subcomment: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ'
        })


def render_comment_html(comment, user):
    """Render HTML for a single comment"""
    from django.template.loader import render_to_string
    return render_to_string('website/courses/components/_comment_item.html', {
        'comment': comment,
        'user': user,
        'course': comment.course
    })


def render_reply_html(reply, user):
    """Render HTML for a single reply"""
    from django.template.loader import render_to_string
    return render_to_string('website/courses/components/_reply_item.html', {
        'reply': reply,
        'user': user,
        'course': reply.comment.course
    })


def render_discussion_reply_html(reply, user):
    """Render HTML for a single reply in discussions page"""
    from django.utils.html import escape
    
    # Get user info safely
    first_name = reply.user.first_name or reply.user.username
    first_letter = first_name[0].upper() if first_name else 'U'
    full_name = reply.user.get_full_name() or reply.user.username
    
    # Check if user is teacher/admin
    is_teacher = hasattr(reply.user, 'profile') and reply.user.profile.status in ['Teacher', 'Admin']
    teacher_badge = '<span class="badge bg-warning text-dark ms-1"><i class="fas fa-chalkboard-teacher"></i> مدرس</span>' if is_teacher else ''
    
    # Escape content to prevent XSS
    content = escape(reply.content).replace('\n', '<br>')
    
    return f'''
    <div class="reply-item mb-2 p-2 bg-light rounded">
        <div class="d-flex align-items-center mb-1">
            <div class="avatar-circle-sm me-2">
                {first_letter}
            </div>
            <strong class="me-2">{escape(full_name)}</strong>
            {teacher_badge}
            <span class="text-muted small">الآن</span>
        </div>
        <div class="small">{content}</div>
    </div>
    '''

@login_required
def discussions_list(request):
    """View all discussions/comments for the current user"""
    profile = request.user.profile
    
    if profile.status == 'Student':
        # Get comments from courses the student is enrolled in
        enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        comments = Comment.objects.filter(course_id__in=enrolled_courses, is_active=True).select_related('user', 'course').prefetch_related('replies', 'likes').order_by('-created_at')
        
        # Get user's own comments
        user_comments = Comment.objects.filter(user=request.user, is_active=True).select_related('course').prefetch_related('replies').order_by('-created_at')
        
    elif profile.status in ['Teacher', 'Admin']:
        # Get comments from teacher's courses
        teacher_courses = Course.objects.filter(teacher__profile__user=request.user).values_list('id', flat=True)
        comments = Comment.objects.filter(course_id__in=teacher_courses, is_active=True).select_related('user', 'course').prefetch_related('replies', 'likes').order_by('-created_at')
        
        # Get user's own comments
        user_comments = Comment.objects.filter(user=request.user, is_active=True).select_related('course').prefetch_related('replies').order_by('-created_at')
    else:
        comments = Comment.objects.none()
        user_comments = Comment.objects.none()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(comments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's liked comments for proper UI state
    user_liked_comments = []
    if page_obj.object_list:
        user_liked_comments = CommentLike.objects.filter(
            user=request.user,
            comment__in=page_obj.object_list
        ).values_list('comment_id', flat=True)
    
    context = {
        'comments': page_obj,
        'user_comments': user_comments[:5],  # Show recent 5 user comments
        'profile': profile,
        'total_comments': comments.count(),
        'user_liked_comments': list(user_liked_comments),
    }
    
    return render(request, 'website/discussions/discussions_list.html', context)


@login_required
def reviews_list(request):
    """View all reviews for the current user"""
    profile = request.user.profile
    
    if profile.status == 'Student':
        # Get user's own reviews
        user_reviews = CourseReview.objects.filter(user=request.user).select_related('course').order_by('-created_at')
        
        # Get reviews on courses the student is enrolled in (for reading)
        enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        course_reviews = CourseReview.objects.filter(course_id__in=enrolled_courses).select_related('user', 'course').order_by('-created_at')
        
        # If no reviews found in enrolled courses, show all reviews (for students to see what others say)
        if course_reviews.count() == 0:
            course_reviews = CourseReview.objects.all().select_related('user', 'course').order_by('-created_at')
        
    elif profile.status in ['Teacher', 'Admin']:
        # Get reviews on teacher's courses
        teacher_courses = Course.objects.filter(teacher__profile__user=request.user).values_list('id', flat=True)
        course_reviews = CourseReview.objects.filter(course_id__in=teacher_courses).select_related('user', 'course').order_by('-created_at')
        
        # Get user's own reviews (if teacher also takes courses)
        user_reviews = CourseReview.objects.filter(user=request.user).select_related('course').order_by('-created_at')
        
        # If no reviews found on teacher's courses, show all reviews for better UX
        if course_reviews.count() == 0:
            course_reviews = CourseReview.objects.all().select_related('user', 'course').order_by('-created_at')
            
    else:
        user_reviews = CourseReview.objects.none()
        course_reviews = CourseReview.objects.none()
    
    # Pagination for course reviews
    from django.core.paginator import Paginator
    paginator = Paginator(course_reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate average rating for teacher's courses
    avg_rating = 0
    if profile.status in ['Teacher', 'Admin'] and course_reviews.exists():
        from django.db.models import Avg
        avg_rating = course_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'course_reviews': page_obj,
        'user_reviews': user_reviews,
        'profile': profile,
        'total_reviews': course_reviews.count(),
        'avg_rating': round(avg_rating, 1),
        'user_total_reviews': user_reviews.count(),
        'all_reviews': course_reviews,  # Add non-paginated reviews for template checks
    }
    
    return render(request, 'website/reviews/reviews_list.html', context)


@login_required
def user_discussions(request):
    """View user's own discussions/comments"""
    user_comments = Comment.objects.filter(user=request.user, is_active=True).select_related('course').prefetch_related('replies').order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(user_comments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'comments': page_obj,
        'total_comments': user_comments.count(),
        'profile': request.user.profile,
    }
    
    return render(request, 'website/discussions/user_discussions.html', context)


@login_required
def user_reviews(request):
    """View user's own reviews"""
    user_reviews = CourseReview.objects.filter(user=request.user).select_related('course').order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(user_reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate user's average rating
    from django.db.models import Avg
    avg_rating = user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'reviews': page_obj,
        'total_reviews': user_reviews.count(),
        'avg_rating': round(avg_rating, 1),
        'profile': request.user.profile,
    }
    
    return render(request, 'website/reviews/user_reviews.html', context)

def verify_certificate(request, verification_code):
    """التحقق من صحة الشهادة باستخدام رمز التحقق"""
    try:
        certificate = get_object_or_404(Certificate, verification_code=verification_code)
        
        context = {
            'certificate': certificate,
            'course': certificate.course,
            'template': certificate.get_template_or_default(),
            'is_valid': certificate.is_valid(),
            'verification_successful': True,
        }
        
        return render(request, 'website/certificate_verification.html', context)
        
    except Certificate.DoesNotExist:
        context = {
            'verification_successful': False,
            'error_message': 'رمز التحقق غير صحيح أو الشهادة غير موجودة.'
        }
        return render(request, 'website/certificate_verification.html', context)
