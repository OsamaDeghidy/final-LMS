from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Course, Video, Module, Notes, Comment, Enrollment
from django.contrib.auth.models import User
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.db.models import Avg

from .models import Category, Course, Module, Video, Comment, SubComment, Notes, Monitor, Tags, Quiz, Question, Answer, Enrollment, Review, VideoProgress, Cart, CartItem, Assignment, AssignmentSubmission, UserExamAttempt, Article
from user.models import Profile, Student, Organization, Teacher
from .utils import searchCourses

from django.contrib.gis.geoip2 import GeoIP2
from django_user_agents.utils import get_user_agent
import requests

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    # Get the user's profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم. يرجى التواصل مع مسؤول النظام.')
        return redirect('home')
    
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
    
    # Calculate statistics for student dashboard
    completed_courses = sum(1 for e in enrollments if e.completed)
    active_courses = sum(1 for e in enrollments if not e.completed and e.progress > 0)
    courses_registered = len(enrollments)
    
    # Initialize teacher statistics
    total_students = 0
    total_courses = 0
    total_earnings = 0
    
    # If user is a teacher, get teacher-specific stats
    teacher = None
    teacher_courses = []
    
    if profile.status == 'Teacher':
        # Force database refresh to get the latest courses
        from django.db import connection
        connection.close()
        
        # Try to get the teacher
        try:
            teacher = Teacher.objects.get(profile__user=request.user)
        except Teacher.DoesNotExist:
            # Create teacher if it doesn't exist
            teacher = Teacher.objects.create(profile=profile)
            logger.info(f"Created new teacher: {teacher}")
        
        # Get ALL courses (for debugging and to ensure we get all courses)
        all_courses = Course.objects.all()
        logger.debug(f"Total courses in database: {all_courses.count()}")
        
        # IMPORTANT: Force a direct query to get all courses for this teacher
        # This is a more direct approach that should work regardless of any caching issues
        teacher_courses = []
        
        # Loop through all courses and check if they belong to this teacher
        for course in all_courses:
            if course.teacher and course.teacher.id == teacher.id:
                # Add this course to our list
                teacher_courses.append(course)
                logger.debug(f"Found teacher course: {course.name}, ID: {course.id}")
        
        logger.debug(f"Teacher: {teacher}, ID: {teacher.id}")
        logger.debug(f"Found {len(teacher_courses)} courses for this teacher")
        
        # If we still don't have any courses, try creating a test course
        if len(teacher_courses) == 0 and all_courses.count() > 0:
            logger.warning("No courses found for this teacher, but there are courses in the database.")
            logger.warning("This suggests there might be an issue with the teacher-course relationship.")
            
            # For debugging, let's check all courses and their teachers
            for course in all_courses:
                logger.debug(f"Course: {course.name}, Teacher ID: {course.teacher_id if course.teacher else 'None'}")
                
            # If there are no courses at all, let's create a test course for this teacher
            if all_courses.count() == 0:
                try:
                    # Create a test course for this teacher
                    test_course = Course.objects.create(
                        name="Test Course",
                        small_description="This is a test course created automatically",
                        description="Test course description",
                        price=99.99,
                        teacher=teacher,
                        status='published',
                        created_at=datetime.today(),
                        updated_at=datetime.today()
                    )
                    teacher_courses.append(test_course)
                    logger.info(f"Created test course: {test_course.name}, ID: {test_course.id}")
                except Exception as e:
                    logger.error(f"Error creating test course: {e}")
        
        # Make sure teacher_courses is a list, not a QuerySet
        teacher_courses = list(teacher_courses)
            
        # Calculate additional data for each course
        for course in teacher_courses:
            # Count total modules
            course.total_module = course.module_set.count()
            
            # Count total videos
            course.total_videos = sum(module.video_set.count() for module in course.module_set.all())
            
            # Count enrolled students
            course.enrolled_students = course.enrollments.count()
            
            # Calculate rating (example calculation)
            course.rating = 4.5  # Default rating, replace with actual calculation if available
            
            # Set videos time (example)
            course.videos_time = "5h 30m"  # Replace with actual calculation if available
        
        total_courses = len(teacher_courses) if isinstance(teacher_courses, list) else teacher_courses.count()
        
        # Count total students enrolled in teacher's courses
        total_students = Enrollment.objects.filter(course__teacher=teacher).count()
        
        # Calculate total earnings (assuming price field represents earnings)
        total_earnings = sum(getattr(course, 'price', 0) for course in teacher_courses)
    
    context = {
        'profile': profile,
        'enrollments': enrollments,
        'completed_courses': completed_courses,
        'active_courses': active_courses,
        'courses_registered': courses_registered,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_earnings': f'${total_earnings:.2f}',
        'teacher': teacher,
        'courses': teacher_courses if profile.status == 'Teacher' else [],
        'teacher_courses': teacher_courses,  # Add this explicitly
    }
    
    return render(request, 'website/dashboard.html', context)

def batch(iterable, n=1):
    """
    Splits an iterable into batches of size n.
    """
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx:min(ndx + n, length)]
        
def index(request):
    courses = Course.objects.all()
    context = {'courses': courses}
    return render(request, 'website/home.html', context)

def allcourses(request):
    # Get all courses with related teacher and user data for better performance
    courses = Course.objects.select_related(
        'teacher',
        'teacher__profile',
        'teacher__profile__user'
    ).all()
    
    # Apply search if there's a query
    courses, search_query = searchCourses(request)
    
    context = {
        'courses': courses,
        'search_query': search_query
    }
    return render(request, 'website/allcourses.html', context)

def contact(request):   
    return render(request, 'website/contact.html')

def courseviewpagenote(request, course_id, note_id):
    course = get_object_or_404(Course, id=course_id)
    note = get_object_or_404(Notes, id=note_id)
    
    # Check if user is enrolled or has course in cart
    is_enrolled = False
    in_cart = False
    
    if request.user.is_authenticated:
        # Check if user is enrolled
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
        
        if not is_enrolled:
            # Check if course is in user's cart
            try:
                cart = Cart.objects.get(user=request.user)
                in_cart = CartItem.objects.filter(cart=cart, course=course).exists()
            except Cart.DoesNotExist:
                pass
                
        # Track PDF access for progress calculation
        if is_enrolled or in_cart:
            try:
                from .models import PDFAccess
                # Record that the user has accessed this PDF
                PDFAccess.objects.get_or_create(
                    user=request.user,
                    pdf_id=note.id,
                    defaults={'read': True}
                )
                
                # If user is enrolled, update progress
                if is_enrolled:
                    enrollment = Enrollment.objects.get(course=course, student=request.user)
                    from .utils import update_enrollment_progress
                    progress = update_enrollment_progress(enrollment)
            except Exception as e:
                print(f"Error tracking PDF access: {e}")
    
    if not (is_enrolled or in_cart):
        messages.warning(request, 'يجب أن تكون مسجلاً في الدورة لعرض هذا المحتوى')
        return redirect('course_detail', course_id=course_id)
    
    # Get all modules for this course
    modules = course.module_set.all()
    
    # Get all videos for this course
    videos = Video.objects.filter(module__course=course)
    
    # Get all notes for this course
    notes = Notes.objects.filter(module__course=course)
    
    # Get completed items for progress tracking
    completed_videos = []
    completed_pdfs = []
    completed_quizzes = []
    completed_assignments = []
    progress = 0
    
    if request.user.is_authenticated and is_enrolled:
        # Get completed videos
        completed_videos = VideoProgress.objects.filter(
            student=request.user,
            video__module__course=course,
            watched=True
        ).values_list('video_id', flat=True)
        
        # Get completed PDFs
        try:
            from .models import PDFAccess
            completed_pdfs = PDFAccess.objects.filter(
                user=request.user,
                pdf_id__in=notes.values_list('id', flat=True),
                read=True
            ).values_list('pdf_id', flat=True)
        except Exception as e:
            print(f"Error getting completed PDFs: {e}")
            completed_pdfs = []
        
        # Get enrollment progress
        try:
            enrollment = Enrollment.objects.get(course=course, student=request.user)
            progress = enrollment.progress
        except:
            progress = 0
    
    context = {
        'course': course,
        'modules': modules,
        'videos': videos,
        'notes': notes,
        'current_note': note,
        'is_enrolled': is_enrolled,
        'in_cart': in_cart,
        'completed_videos': completed_videos,
        'completed_pdfs': completed_pdfs,
        'completed_quizzes': completed_quizzes,
        'completed_assignments': completed_assignments,
        'progress': progress
    }
    
    return render(request, 'website/courseviewpagenote.html', context)

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    in_cart = False
    
    if request.user.is_authenticated:
        # Check if user is enrolled in the course
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
        
        # Check if course is in user's cart
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            in_cart = CartItem.objects.filter(cart=cart, course=course).exists()
    
    # Get course reviews
    reviews = Review.objects.filter(course=course)
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Round to nearest half
    avg_rating = round(avg_rating * 2) / 2
    
    # Generate full and half stars
    full_stars = int(avg_rating)
    half_star = avg_rating - full_stars > 0
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'in_cart': in_cart,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),
    }
    
    return render(request, 'website/course_detail.html', context)

@login_required
def add_to_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is already enrolled in the course
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, 'أنت مسجل بالفعل في هذه الدورة')
        return redirect('course_detail', course_id=course_id)
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if course is already in cart
    if CartItem.objects.filter(cart=cart, course=course).exists():
        messages.info(request, 'هذه الدورة موجودة بالفعل في سلة التسوق')
    else:
        # Add course to cart
        CartItem.objects.create(cart=cart, course=course)
        messages.success(request, 'تمت إضافة الدورة إلى سلة التسوق')
    
    # Check if the user wants to view the course directly
    next_page = request.GET.get('next', None)
    if next_page and next_page == 'view_course':
        # Clear any pending messages to prevent them from showing up
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Iterating through messages marks them as read
        storage.used = True
        return redirect('courseviewpage', course_id=course_id)
    
    return redirect('view_cart')

@login_required
def view_cart(request):
    # Get or create cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('course', 'course__teacher__profile').all()
    total_price = cart.total_price
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    }
    
    return render(request, 'website/cart.html', context)

@login_required
def remove_from_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Try to find and delete the cart item
    deleted, _ = CartItem.objects.filter(cart=cart, course=course).delete()
    
    if deleted:
        messages.success(request, 'تمت إزالة الدورة من سلة التسوق')
    else:
        messages.warning(request, 'هذه الدورة غير موجودة في سلة التسوق')
    
    return redirect('view_cart')

@login_required
def checkout(request):
    # Get user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'سلة التسوق الخاصة بك فارغة')
        return redirect('view_cart')
    
    if request.method == 'POST':
        # Process payment (placeholder for now)
        # In a real application, you would integrate with a payment gateway here
        
        # Enroll user in all courses in the cart
        enrolled_courses = []
        for cart_item in cart.items.all():
            # Check if already enrolled
            if not Enrollment.objects.filter(course=cart_item.course, student=request.user).exists():
                enrollment = Enrollment.objects.create(
                    course=cart_item.course,
                    student=request.user,
                    status='active'
                )
                enrolled_courses.append(cart_item.course.name)
        
        # Clear the cart after successful enrollment
        cart.items.all().delete()
        
        if enrolled_courses:
            messages.success(request, f'تم الاشتراك في {len(enrolled_courses)} دورة بنجاح!')
        else:
            messages.info(request, 'لم يتم الاشتراك في أي دورات جديدة.')
            
        return redirect('dashboard')
    
    context = {
        'cart_items': cart.items.select_related('course', 'course__teacher__profile').all(),
        'total_price': cart.total_price,
        'cart': cart
    }
    
    return render(request, 'website/checkout.html', context)

def courseviewpage(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    in_cart = False
    enrollment = None
    progress = 0
    completed_videos = []
    completed_quizzes = []
    completed_pdfs = []
    completed_assignments = []
    
    if request.user.is_authenticated:
        # Check if user is enrolled
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
            # Update progress using new system
            from .utils import update_enrollment_progress, get_completed_content_ids
            progress = update_enrollment_progress(enrollment)
            
            # Get completed content using new system
            completed_videos = get_completed_content_ids(request.user, course, 'video')
            completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
            completed_pdfs = get_completed_content_ids(request.user, course, 'note')
            completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
            
            print(f"[DEBUG] Completed content for {request.user.username}:")
            print(f"  - Videos: {completed_videos}")
            print(f"  - PDFs: {completed_pdfs}")
            print(f"  - Quizzes: {completed_quizzes}")
            print(f"  - Assignments: {completed_assignments}")
            print(f"  - Progress: {progress}%")
            
        else:
            # Check if course is in user's cart
            try:
                cart = Cart.objects.get(user=request.user)
                in_cart = CartItem.objects.filter(cart=cart, course=course).exists()
            except (Cart.DoesNotExist, CartItem.DoesNotExist):
                in_cart = False
    
    # Allow access if user is enrolled or has the course in their cart
    if not (is_enrolled or in_cart):
        messages.warning(request, 'يجب أن تكون مسجلاً في الدورة أو أن تكون في سلة التسوق لعرض هذا المحتوى')
        return redirect('course_detail', course_id=course.id)
    
    # Get all modules for the course with related content, ordered properly
    modules = course.module_set.all().prefetch_related(
        'video_set', 'notes_set', 'module_quizzes'
    ).order_by('number')
    
    # Get quizzes and assignments for the course
    quizzes = Quiz.objects.filter(course=course)
    assignments = Assignment.objects.filter(course=course)
    
    # Count different types of content
    quizzes_count = quizzes.count()
    pdfs_count = Notes.objects.filter(module__course=course).count()
    assignments_count = assignments.count()
    
    # Get content from URL parameters if provided
    content_type = request.GET.get('content_type')
    content_id = request.GET.get('content_id')
    
    # Build a comprehensive list of all content items in order
    all_content = []
    for module in modules:
        # Add videos ordered by number
        for video in module.video_set.all().order_by('number'):
            all_content.append({
                'type': 'video',
                'content': video,
                'module': module
            })
        
        # Add notes (PDFs) ordered by number
        for note in module.notes_set.all().order_by('number'):
            all_content.append({
                'type': 'note',
                'content': note,
                'module': module
            })
        
        # Add module PDFs if they exist
        if module.module_pdf:
            # Create a pseudo-note for module PDF
            module_pdf_note = type('obj', (object,), {
                'id': f'module_pdf_{module.id}',
                'description': f'ملف PDF - {module.name}',
                'file': module.module_pdf,
                'module': module
            })()
            all_content.append({
                'type': 'note',
                'content': module_pdf_note,
                'module': module
            })
        
        if module.additional_materials:
            # Create a pseudo-note for additional materials
            additional_note = type('obj', (object,), {
                'id': f'additional_materials_{module.id}',
                'description': f'مواد إضافية - {module.name}',
                'file': module.additional_materials,
                'module': module
            })()
            all_content.append({
                'type': 'note',
                'content': additional_note,
                'module': module
            })
        
        # Add quizzes that belong to this module
        for quiz in module.module_quizzes.all():
                all_content.append({
                    'type': 'quiz',
                    'content': quiz,
                    'module': module
                })
        
        # Add assignments that belong to this module
        for assignment in assignments.filter(module=module):
                all_content.append({
                    'type': 'assignment',
                    'content': assignment,
                    'module': module
                })
    
    # Initialize content navigation
    current_content = None
    prev_content = None
    next_content = None
    
    # Find the current content based on URL parameters or default to first item
    if content_type and content_id:
        # Try to find the specified content
        for i, item in enumerate(all_content):
            content_item_id = str(item['content'].id)
            if item['type'] == content_type and content_item_id == content_id:
                current_content = item
                # Set previous content if not first item
                if i > 0:
                    prev_content = all_content[i-1]
                # Set next content if not last item
                if i < len(all_content) - 1:
                    next_content = all_content[i+1]
                break
    
    # If no content was found or specified, use the first item
    if not current_content and all_content:
        current_content = all_content[0]
        if len(all_content) > 1:
            next_content = all_content[1]
    
    # Calculate course statistics
    total_videos = sum(module.video_set.count() for module in modules)
    total_notes = sum(module.notes_set.count() for module in modules)
    
    # Add module PDFs to total notes count
    total_notes += Module.objects.filter(course=course, module_pdf__isnull=False).count()
    total_notes += Module.objects.filter(course=course, additional_materials__isnull=False).count()
    
    total_quizzes = sum(module.module_quizzes.count() for module in modules)
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'progress': progress,
        'modules': modules,
        'quizzes': quizzes,
        'assignments': assignments,
        'current_content': current_content,
        'prev_content': prev_content,
        'next_content': next_content,
        'completed_videos': completed_videos,
        'completed_quizzes': completed_quizzes,
        'completed_pdfs': completed_pdfs,
        'completed_assignments': completed_assignments,
        'quizzes_count': quizzes_count,
        'pdfs_count': pdfs_count,
        'assignments_count': assignments_count,
        'all_content': all_content,
        'total_videos': total_videos,
        'total_notes': total_notes,
        'total_quizzes': total_quizzes,
        'is_enrolled': is_enrolled,
        'in_cart': in_cart
    }
    
    return render(request, 'website/courseviewpage.html', context)

def courseviewpagevideo(request, course_id, video_id):
    course = get_object_or_404(Course, id=course_id)
    video = get_object_or_404(Video, id=video_id)
    is_enrolled = False
    enrollment = None
    video_progress = None
    completed_videos = []
    
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
            # Update last accessed time
            enrollment.last_accessed = timezone.now()
            enrollment.save(update_fields=['last_accessed'])
            
            # Get or create video progress
            video_progress, created = VideoProgress.objects.get_or_create(
                student=request.user,
                video=video,
                defaults={'watched': False}
            )
            
            # Get completed videos
            completed_videos = VideoProgress.objects.filter(
                student=request.user,
                video__course=course,
                watched=True
            ).values_list('video_id', flat=True)
            
    if not is_enrolled:
        return redirect('course_detail', course_id=course.id)
    
    # Get all modules for the course
    modules = course.module_set.all().prefetch_related('video_set', 'notes_set')
    
    # Build a list of all content items (videos and notes) in order
    all_content = []
    for module in modules:
        for v in module.video_set.all():
            all_content.append({
                'type': 'video',
                'content': v,
                'module': module
            })
        for note in module.notes_set.all():
            all_content.append({
                'type': 'note',
                'content': note,
                'module': module
            })
    
    # Sort content by module number and then by content number
    all_content.sort(key=lambda x: (x['module'].number or 0, 
                                   x['content'].number if hasattr(x['content'], 'number') else 0))
    
    # Find current content index
    current_index = -1
    current_content = None
    for i, content in enumerate(all_content):
        if content['type'] == 'video' and content['content'].id == video.id:
            current_index = i
            current_content = content
            break
    
    # Set previous and next content
    prev_content = all_content[current_index - 1] if current_index > 0 else None
    next_content = all_content[current_index + 1] if current_index < len(all_content) - 1 else None
    
    # Get quiz for this video if exists
    quiz = Quiz.objects.filter(video=video).first()
    questions = quiz.question_set.all() if quiz else []
    
    context = {
        'course': course, 
        'video': video, 
        'questions': questions, 
        'quiz': quiz,
        'video_progress': video_progress,
        'modules': modules,
        'current_content': current_content,
        'prev_content': prev_content,
        'next_content': next_content,
        'completed_videos': completed_videos,
        'all_content': all_content,
        'progress': enrollment.progress
    }
    
    return render(request, 'website/courseviewpage.html', context)

@login_required  
@require_POST
def submit_quiz(request):
    """Handle quiz submission"""
    try:
        quiz_id = request.POST.get('quiz_id')
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Calculate score
        total_questions = quiz.question_set.count()
        correct_answers = 0
        
        for question in quiz.question_set.all():
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        correct_answers += 1
                except Answer.DoesNotExist:
                    pass
        
        # Calculate percentage
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Check if passed
        pass_mark = getattr(quiz, 'pass_mark', 60)
        passed = score_percentage >= pass_mark
        
        # Save exam attempt
        try:
            UserExamAttempt.objects.create(
                user=request.user,
                exam=quiz,
                score=score_percentage,
                passed=passed
            )
        except Exception:
            pass
        
        # Update progress if passed
        if passed:
            enrollment = Enrollment.objects.filter(
                course=quiz.course,
                student=request.user
            ).first()
            
            if enrollment:
                from .utils import update_enrollment_progress
                progress = update_enrollment_progress(enrollment)
        
        # Redirect to results page or back to course
        if passed:
            messages.success(request, f'تهانينا! لقد نجحت في الاختبار بدرجة {score_percentage:.1f}%')
        else:
            messages.warning(request, f'لم تنجح في الاختبار. حصلت على {score_percentage:.1f}% والمطلوب {pass_mark}%')
        
        return redirect('courseviewpage', course_id=quiz.course.id)
        
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تسليم الاختبار: {str(e)}')
        return redirect('courseviewpage', course_id=quiz.course.id)

def courseviewpagenote(request, course_id, note_id):
    course = get_object_or_404(Course, id=course_id)
    note = get_object_or_404(Notes, id=note_id)
    is_enrolled = False
    enrollment = None
    completed_videos = []
    
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
            # Update last accessed time
            enrollment.last_accessed = timezone.now()
            enrollment.save(update_fields=['last_accessed'])
            
            # Get completed videos
            completed_videos = VideoProgress.objects.filter(
                student=request.user,
                video__course=course,
                watched=True
            ).values_list('video_id', flat=True)
    
    if not is_enrolled:
        return redirect('course_detail', course_id=course.id)
    
    # Get all modules for the course
    modules = course.module_set.all().prefetch_related('video_set', 'notes_set')
    
    # Build a list of all content items (videos and notes) in order
    all_content = []
    for module in modules:
        for video in module.video_set.all():
            all_content.append({
                'type': 'video',
                'content': video,
                'module': module
            })
        for n in module.notes_set.all():
            all_content.append({
                'type': 'note',
                'content': n,
                'module': module
            })
    
    # Sort content by module number and then by content number
    all_content.sort(key=lambda x: (x['module'].number or 0, 
                                   x['content'].number if hasattr(x['content'], 'number') else 0))
    
    # Find current content index
    current_index = -1
    current_content = None
    for i, content in enumerate(all_content):
        if content['type'] == 'note' and content['content'].id == note.id:
            current_index = i
            current_content = content
            break
    
    # Set previous and next content
    prev_content = all_content[current_index - 1] if current_index > 0 else None
    next_content = all_content[current_index + 1] if current_index < len(all_content) - 1 else None
    
    context = {
        'course': course, 
        'note': note,
        'modules': modules,
        'current_content': current_content,
        'prev_content': prev_content,
        'next_content': next_content,
        'completed_videos': completed_videos,
        'all_content': all_content,
        'progress': enrollment.progress
    }
    
    return render(request, 'website/courseviewpage.html', context)

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('index')  # Ensure 'index' is defined in URLs
    else:
        try:
            profile = Profile.objects.get(user=request.user)
            
            # Get enrollments for students
            enrollments = []
            if profile.status == 'Student':
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
            
            # Query all courses to display in the dashboard (for teachers/admins)
            courses = Course.objects.all()
            
            context = {
                "profile": profile,
                "courses": courses,
                "enrollments": enrollments
            }
            return render(request, 'website/dashboard.html', context)
        except Profile.DoesNotExist:
            return HttpResponse('Profile does not exist for the user.')
        except Profile.MultipleObjectsReturned:
            return HttpResponse('Multiple profiles found for the user. Please contact support.')

def create_course(request):
    if request.user.profile.status == 'Teacher':
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description')
            image_course = request.FILES.get('image_course')
            syllabus_pdf = request.FILES.get('syllabus_pdf')
            materials_pdf = request.FILES.get('materials_pdf')
            price = request.POST.get('price')
            small_description = request.POST.get('small_description')
            learned = request.POST.get('learned')

            tags_input = request.POST.get('tags')
            tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

            tags = []
            for tag_name in tags_list:
                tag, created = Tags.objects.get_or_create(name=tag_name)
                tags.append(tag)
            try:
                teacher = Teacher.objects.get(profile=request.user.profile)
                # Create the course with the teacher explicitly assigned
                course = Course(
                    name=name,
                    description=description,
                    image_course=image_course,
                    syllabus_pdf=syllabus_pdf,
                    materials_pdf=materials_pdf,
                    price=price,
                    small_description=small_description,
                    learned=learned,
                    teacher=teacher,  # Explicitly assign the teacher
                    organization=teacher.organization,
                    created_at=datetime.today(),
                    updated_at=datetime.today(),
                    status='published'  # Set status to published by default
                )
                course.save()
                
                # Print debug info - use encoding to avoid character issues
                try:
                    print(f"Created course with ID: {course.id}")
                    print(f"Teacher ID: {teacher.id}")
                except UnicodeEncodeError:
                    print(f"Created course with ID: {course.id} (name contains non-ASCII characters)")
                    print(f"Teacher ID: {teacher.id}")
                course.tags.set(tags)
                
                # Process modules and quizzes
                module_keys = [key for key in request.POST.keys() if key.startswith('module_name_module_')]
                module_ids = [key.split('module_name_module_')[1] for key in module_keys]
                
                for module_id in module_ids:
                    module_name = request.POST.get(f'module_name_module_{module_id}')
                    if not module_name:
                        continue
                    
                    # Create module
                    module = Module(
                        name=module_name,
                        course=course,
                        number=course.total_module + 1
                    )
                    module.save()
                    course.total_module += 1
                    
                    # Process module videos
                    module_videos = request.FILES.getlist(f'module_videos_module_{module_id}')
                    video_names = []
                    
                    # Get video names
                    video_name_keys = [k for k in request.POST.keys() if k.startswith(f'video_name_module_{module_id}_')]
                    for key in video_name_keys:
                        video_name = request.POST.get(key)
                        if video_name and video_name.strip():
                            video_names.append(video_name)
                    
                    # Create videos
                    for i, video in enumerate(module_videos):
                        video_name = video_names[i] if i < len(video_names) else video.name.split('.')[0]
                        Video.objects.create(
                            name=video_name,
                            module=module,
                            course=course,
                            video=video,
                            number=i+1
                        )
                    
                    # Process module notes
                    note_keys = [k for k in request.POST.keys() if k.startswith(f'module_notes_module_{module_id}_')]
                    for i, key in enumerate(note_keys):
                        note_text = request.POST.get(key)
                        if note_text and note_text.strip():
                            module.total_notes += 1
                            Notes.objects.create(
                                user=request.user,
                                module=module,
                                description=note_text,
                                number=module.total_notes
                            )
                    
                    # Process quiz if exists
                    has_quiz = request.POST.get(f'has_quiz_module_{module_id}')
                    if has_quiz == 'on':
                        quiz_title = request.POST.get(f'quiz_title_module_{module_id}')
                        quiz_description = request.POST.get(f'quiz_description_module_{module_id}')
                        quiz_pass_mark = request.POST.get(f'quiz_pass_mark_module_{module_id}', 50)
                        quiz_time_limit = request.POST.get(f'quiz_time_limit_module_{module_id}', 10)
                        
                        # Create quiz
                        quiz = Quiz.objects.create(
                            title=quiz_title,
                            description=quiz_description,
                            module=module,
                            course=course,
                            quiz_type='module',
                            pass_mark=float(quiz_pass_mark),
                            time_limit=int(quiz_time_limit),
                            is_active=True
                        )
                        
                        # Process questions
                        question_text_keys = [k for k in request.POST.keys() if k.startswith(f'question_text_module_{module_id}_')]
                        for key in question_text_keys:
                            question_index = key.split(f'question_text_module_{module_id}_')[1]
                            question_text = request.POST.get(key)
                            if not question_text or not question_text.strip():
                                continue
                                
                            question_type = request.POST.get(f'question_type_module_{module_id}_{question_index}')
                            
                            # Create question
                            question = Question.objects.create(
                                quiz=quiz,
                                text=question_text,
                                question_type=question_type,
                                points=1,
                                order=int(question_index) if question_index.isdigit() else 0
                            )
                            
                            # Process answers based on question type
                            if question_type == 'short_answer':
                                # For short answer, create a single answer
                                answer_text = request.POST.get(f'answer_short_question_module_{module_id}_{question_index}')
                                if answer_text:
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_text,
                                        is_correct=True,
                                        order=0
                                    )
                            else:
                                # For multiple choice or true/false
                                correct_answer = request.POST.get(f'correct_answer_question_module_{module_id}_{question_index}')
                                
                                # Get all answers for this question
                                answer_keys = [k for k in request.POST.keys() if k.startswith(f'answer_text_question_module_{module_id}_{question_index}_')]
                                
                                for answer_key in answer_keys:
                                    answer_index = answer_key.split('_')[-1]
                                    answer_text = request.POST.get(answer_key)
                                    
                                    if answer_text and answer_text.strip():
                                        is_correct = (correct_answer == answer_index)
                                        Answer.objects.create(
                                            question=question,
                                            text=answer_text,
                                            is_correct=is_correct,
                                            order=int(answer_index) if answer_index.isdigit() else 0
                                        )
                
                course.save()
                return redirect('course_detail', course_id=course.id)
            except ObjectDoesNotExist:
                return HttpResponse("Error: Teacher matching query does not exist.", status=404)
            except Exception as e:
                return HttpResponse(f"Error creating course: {str(e)}", status=500)
        
        # Get the profile for the dashboard_base.html template
        profile = Profile.objects.get(user=request.user)
        categories = Category.objects.all()
        context = {"profile": profile, "categories": categories}
        return render(request, 'website/create_course.html', context)
    else:
        return redirect('index')

def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    monitor = None
    user_review = None
    is_enrolled = False
    profile_context = {"status": "none"}  # Initialize profile_context with a default value
    
    if request.user.is_authenticated:
        # Check if user is enrolled in the course
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
            
        # Get user's review if it exists
        user_review = Review.objects.filter(course=course, user=request.user).first()
        
        # Get user profile information
        try:
            profile = Profile.objects.get(user=request.user)
            profile_context = profile
        except Profile.DoesNotExist:
            pass
            
        try:
            monitor = Monitor.objects.get(user=request.user, landing_page=request.META.get('HTTP_HOST') + request.META.get('PATH_INFO'), ip=request.META.get('REMOTE_ADDR'))
            monitor.frequency += 1
            monitor.save()
        except Monitor.DoesNotExist:
            pass
    else:
        monitor = Monitor()
        monitor.ip = request.META.get('REMOTE_ADDR')
        g = 'https://geolocation-db.com/jsonp/' + str(monitor.ip)
        response = requests.get(g)
        data = response.content.decode()
        data = data.split("(")[1].strip(")")
        location = json.loads(data)
        monitor.country = location['country_name']
    
    # Process review submission
    if request.method == 'POST' and request.user.is_authenticated and 'review_rating' in request.POST:
        rating = int(request.POST.get('review_rating'))
        comment = request.POST.get('review_comment', '')
        
        # Create or update review
        if user_review:
            user_review.rating = rating
            user_review.comment = comment
            user_review.save()
            messages.success(request, 'تم تحديث تقييمك بنجاح!')
        else:
            Review.objects.create(
                course=course,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'تم إضافة تقييمك بنجاح!')
        
        # Refresh user review after submission
        user_review = Review.objects.filter(course=course, user=request.user).first()
    
    # Get all modules for this course with their videos
    modules = Module.objects.filter(course=course).order_by('number').prefetch_related('video_set')
    
    # Get course reviews
    reviews = Review.objects.filter(course=course).select_related('user')
    
    # Check if the user is a teacher and if they own this course
    is_owner = False
    if request.user.is_authenticated:
        try:
            teacher = Teacher.objects.get(profile__user=request.user)
            if teacher == course.teacher:
                is_owner = True
        except Teacher.DoesNotExist:
            pass
    
    context = {
        "profile": profile_context, 
        "course": course,
        "modules": modules,
        "reviews": reviews,
        "user_review": user_review,
        "is_enrolled": is_enrolled,
        "is_owner": is_owner
    }        
    return render(request, 'website/course_detail.html', context)

def update_course(request, course_id):
    import json
    from django.http import JsonResponse
    from django.urls import reverse
    import logging
    
    logger = logging.getLogger(__name__)
    
    course = get_object_or_404(Course, pk=course_id)
    
    # Check if user has permission to edit this course
    if not (course.teacher and course.teacher.profile == request.user.profile):
        messages.error(request, 'ليس لديك صلاحية لتعديل هذه الدورة')
        return redirect('course_detail', course_id=course_id)
    
    # Get user profile and student data
    profile = get_object_or_404(Profile, user=request.user)
    student = None
    try:
        student = Student.objects.get(profile=profile)
    except Student.DoesNotExist:
        pass  # User might be a teacher, not a student
    
    # Get all modules associated with this course
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Ensure course has at least one module
    if not modules.exists():
        ensure_course_has_module(course)
        modules = Module.objects.filter(course=course).order_by('number')
    
    # Get categories and organizations for the form
    categories = Category.objects.all()
    organizations = Organization.objects.all()
    
    # Create JSON data for modules
    modules_json = {}
    for module in modules:
        videos = [{'id': video.id, 'name': video.name} for video in module.video_set.all()]
        modules_json[str(module.id)] = {
            'id': module.id,
            'name': module.name,
            'description': module.description or '',
            'videos': videos,
            'total_video': module.total_video,
            'duration': module.duration or ''
        }
    
    # Prepare tags string for the form
    tags_string = ", ".join([tag.name for tag in course.tags.all()])
    
    if request.method == 'POST':
        try:
            # Update basic course information
            course.name = request.POST.get('name', course.name)
            course.description = request.POST.get('description', course.description)
            course.price = request.POST.get('price', course.price)
            course.small_description = request.POST.get('small_description', course.small_description)
            course.learned = request.POST.get('learned', course.learned)
            course.level = request.POST.get('level', course.level)
            course.updated_at = datetime.today()
            
            # Update category if provided
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = Category.objects.get(pk=category_id)
                    course.category = category
                except Category.DoesNotExist:
                    logger.warning(f"Category with ID {category_id} not found")
            
            # Handle image upload
            if 'image_course' in request.FILES:
                course.image_course = request.FILES['image_course']
                
            # Handle PDF uploads
            if 'syllabus_pdf' in request.FILES:
                if course.syllabus_pdf:
                    course.syllabus_pdf.delete(save=False)
                course.syllabus_pdf = request.FILES['syllabus_pdf']
            elif request.POST.get('delete_syllabus_pdf') == '1':
                if course.syllabus_pdf:
                    course.syllabus_pdf.delete(save=False)
                    course.syllabus_pdf = None
                    
            if 'materials_pdf' in request.FILES:
                if course.materials_pdf:
                    course.materials_pdf.delete(save=False)
                course.materials_pdf = request.FILES['materials_pdf']
            elif request.POST.get('delete_materials_pdf') == '1':
                if course.materials_pdf:
                    course.materials_pdf.delete(save=False)
                    course.materials_pdf = None

            # Handle tags
            tags_input = request.POST.get('tags', '')
            course.tags.clear()
            if tags_input:
                tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tags_list:
                    tag, created = Tags.objects.get_or_create(name=tag_name)
                    course.tags.add(tag)
            
            # Save course first
            course.save()
            logger.info(f"Course {course_id} basic info updated successfully")
            
            # Update course totals
            course.total_module = course.module_set.count()
            course.save()
            
            messages.success(request, 'تم تحديث الدورة بنجاح')
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == 'true':
                return JsonResponse({
                    'success': True, 
                    'message': 'تم تحديث الدورة بنجاح',
                    'redirect_url': reverse('course_detail', args=[course_id])
                })
            else:
                return redirect('course_detail', course_id=course.id)
                
        except Exception as e:
            logger.error(f"Error updating course {course_id}: {str(e)}")
            messages.error(request, f'حدث خطأ أثناء تحديث الدورة: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return render(request, 'website/update_course.html', {
        'course': course, 
        'modules': modules,
        'modules_json': json.dumps(modules_json),
        'profile': profile,
        'student': student,
        'categories': categories,
        'organizations': organizations,
        'tags_string': tags_string
    })

def _process_quiz_questions(request, quiz, module_prefix):
    """Helper function to process quiz questions for both new and existing modules"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get all question text fields for this quiz
    question_keys = [key for key in request.POST.keys() if key.startswith(f'question_text_{module_prefix}_')]
    
    for question_key in question_keys:
        # Extract question index from key
        question_index = question_key.replace(f'question_text_{module_prefix}_', '')
        question_text = request.POST.get(question_key)
        
        if not question_text or not question_text.strip():
            continue
        
        question_type = request.POST.get(f'question_type_{module_prefix}_{question_index}', 'multiple_choice')
        
        # Create or update question
        question = Question.objects.create(
            quiz=quiz,
            text=question_text,
            question_type=question_type,
            points=1,
            order=int(question_index) if question_index.isdigit() else 0
        )
        
        # Process answers based on question type
        if question_type == 'multiple_choice':
            correct_answer = request.POST.get(f'correct_answer_{module_prefix}_{question_index}')
            
            # Get all answers for this question
            answer_keys = [k for k in request.POST.keys() if k.startswith(f'answer_text_{module_prefix}_{question_index}_')]
            
            for answer_key in answer_keys:
                answer_index = answer_key.split('_')[-1]
                answer_text = request.POST.get(answer_key)
                
                if answer_text and answer_text.strip():
                    is_correct = (correct_answer == answer_index)
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=is_correct,
                        order=int(answer_index) if answer_index.isdigit() else 0
                    )
        
        elif question_type == 'true_false':
            correct_answer = request.POST.get(f'correct_answer_{module_prefix}_{question_index}')
            
            # Create True answer
            Answer.objects.create(
                question=question,
                text="صح",
                is_correct=correct_answer == '0',
                order=0
            )
            
            # Create False answer
            Answer.objects.create(
                question=question,
                text="خطأ",
                is_correct=correct_answer == '1',
                order=1
            )
        
        elif question_type == 'short_answer':
            answer_text = request.POST.get(f'answer_short_{module_prefix}_{question_index}', '')
            Answer.objects.create(
                question=question,
                text=answer_text,
                is_correct=True,
                order=0
            )
        
        logger.info(f"Created question {question.id} for quiz {quiz.id}")

def delete_course(request):
    if request.method == 'POST':
        try:
            # Try to parse JSON data (for AJAX requests)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                course_id = data.get('course_id')
            else:
                # Handle form data (for regular form submissions)
                course_id = request.POST.get('course_id')
                
            if not course_id:
                return JsonResponse({'error': 'Course ID is required'}, status=400)
                
            course = get_object_or_404(Course, id=course_id)
            
            # Check if user has permission to delete this course
            if hasattr(request.user, 'profile') and hasattr(course, 'teacher') and course.teacher.profile == request.user.profile:
                course.delete()
                if request.content_type == 'application/json':
                    return JsonResponse({'success': True, 'message': 'Course deleted successfully'})
                else:
                    return redirect('dashboard')
            else:
                if request.content_type == 'application/json':
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                else:
                    return redirect('course_detail', course_id=course_id)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

def course(request):
    teacher=get_object_or_404(Teacher,profile=request.user.profile)
    courses=Course.objects.filter(teacher=teacher)
    context={
        "courses":courses,
    }
    return render(request,'website/courses.html', context)

def create_module(request, course_id):
    course = Course.objects.get(id=course_id)
    
    # Get user profile and student data
    profile = get_object_or_404(Profile, user=request.user)
    student = None
    try:
        student = Student.objects.get(profile=profile)
    except Student.DoesNotExist:
        pass  # User might be a teacher, not a student
    
    course.total_module += 1

    if request.method == 'POST':
        module_name = request.POST['module_name']
        module_number = course.total_module
        module = Module()
        module.name = module_name
        module.course = course
        module.number = module_number
        module.save()
        number = 0
        
        # Handle video uploads
        for video in request.FILES.getlist('video'):
            video_name = video.name.split('.')[0]
            number += 1
            Video.objects.create(module=module, video=video, name=video_name, course=course, number=number)


        # Handle notes
        for note in request.POST.getlist('notes[]'):
            if note.strip():
                module.total_notes += 1
                Notes.objects.create(user=request.user, module=module, description=note, number=module.total_notes)

        # Handle quiz creation if exists
        quiz_title = request.POST.get('quiz_title')
        if quiz_title:
            quiz = Quiz.objects.create(
                title=quiz_title,
                description=request.POST.get('quiz_description', ''),
                module=module,
                course=course,
                quiz_type='module',
                time_limit=int(request.POST.get('quiz_time_limit', 10)),
                pass_mark=float(request.POST.get('quiz_pass_mark', 50)),
                is_active=True
            )
            
            # Process questions
            for i, question_text in enumerate(request.POST.getlist('question_text[]')):
                if not question_text.strip():
                    continue
                    
                question_type = request.POST.getlist('question_type[]')[i]
                question = Question.objects.create(
                    quiz=quiz,
                    text=question_text,
                    question_type=question_type,
                    points=1,
                    order=i
                )
                
                if question_type == 'short_answer':
                    # For short answer, create a single answer
                    answer_text = request.POST.get(f'answer_short_{i}')
                    if answer_text:
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=True,
                            order=0
                        )
                else:
                    # For multiple choice or true/false
                    answer_index = 0
                    while True:
                        answer_key = f'answer_text_{i}_{answer_index}'
                        if answer_key in request.POST:
                            answer_text = request.POST[answer_key]
                            is_correct = False
                            
                            if question_type == 'true_false':
                                # For true/false, check if this is the selected radio
                                correct_answer = request.POST.get(f'correct_answer_{i}')
                                is_correct = (correct_answer == str(answer_index))
                            else:
                                # For multiple choice, check radio button
                                correct_answer = request.POST.get(f'correct_answer_{i}')
                                is_correct = (correct_answer == str(answer_index))
                            
                            Answer.objects.create(
                                question=question,
                                text=answer_text,
                                is_correct=is_correct,
                                order=answer_index
                            )
                            answer_index += 1
                        else:
                            break
        
        course.save()
        return redirect('course_modules', course_id=course_id)

    return render(request, 'website/create_module.html', {
        'course': course,
        'profile': profile,
        'student': student
    })

def update_module(request, course_id, module_id):
    course = Course.objects.get(id=course_id)
    module = Module.objects.get(id=module_id)

    if request.method == 'POST':
        # Check if this is an AJAX request from the update_course page
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'videos' in request.FILES:
            # Handle AJAX request from update_course page
            module_name = request.POST.get('name', '')
            if module_name:
                module.name = module_name
                module.save()
            
            # Get video names from the AJAX request - handle both parameter formats
            video_names = []
            if 'video_names[]' in request.POST:
                video_names = request.POST.getlist('video_names[]')
            elif 'video_names' in request.POST:
                video_names = request.POST.getlist('video_names')
            
            # Handle video uploads
            videos = []
            if 'videos' in request.FILES:
                videos = request.FILES.getlist('videos')
            elif 'video' in request.FILES:
                videos = request.FILES.getlist('video')
                
            for i, video in enumerate(videos):
                # Use provided video name if available, otherwise use the file name
                video_name = video_names[i] if i < len(video_names) else video.name.split('.')[0]
                Video.objects.create(module=module, video=video, name=video_name, course=course)
            
            # Return JSON response for AJAX request
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'message': 'Module updated successfully'})
        else:
            # Handle regular form submission
            module_name = request.POST.get('module_name', '')
            module.name = module_name
            module.save()

            videos_to_delete = request.POST.getlist('delete_video')
            for video_id in videos_to_delete:
                Video.objects.filter(id=video_id).delete()

            for video in request.FILES.getlist('video'):
                video_name = video.name.split('.')[0]
                Video.objects.create(module=module, video=video, name=video_name, course=course)

            notes_to_delete = request.POST.getlist('delete_note')
            for note_id in notes_to_delete:
                Notes.objects.filter(id=note_id).delete()

            for note in request.POST.getlist('note'):
                Notes.objects.create(user=request.user, module=module, description=note)

            return redirect('course_modules', course_id=course_id)

    return render(request, 'website/update_module.html', {'course': course, 'module': module})

def delete_module(request, course_id, module_id):
    course = Course.objects.get(id=course_id)
    module = Module.objects.get(id=module_id)

    if request.method == 'POST':
        module.delete()
        return redirect('course_modules', course_id=course_id)

    return render(request, 'website/delete_module.html', {'course': course, 'module': module})

def course_modules(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course)
    context = {
        'course': course,
        'modules': modules,
    }
    return redirect('update_course', course_id=course.id)

def quiz_list(request, video_id):
    quizzes = Quiz.objects.filter(video=video_id)
    return render(request, 'website/quiz_list.html', {'quizzes': quizzes})

def view_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    return render(request, 'website/view_quiz.html', {'quiz': quiz})

from datetime import datetime, timedelta

def create_quiz(request, video_id):
    video = Video.objects.get(id=video_id)
    if request.user.profile != video.module.course.teacher.profile:
        return HttpResponse('You do not have permission to access this page')
    if request.method == 'POST':
        pass_mark = request.POST.get('pass_mark')
        timestamp = request.POST.get('timestamp')
        if timestamp:
            timestamp_parts = [int(part) for part in timestamp.split(':')]
            timestamp_td = timedelta(hours=timestamp_parts[0], minutes=timestamp_parts[1], seconds=timestamp_parts[2])
            timestamp = timestamp_parts[0]*60*60+timestamp_parts[1]*60+timestamp_parts[2]
            start_time = int(timestamp)
            start_time = timedelta(seconds=float(start_time))
        else:
            start_time = 0

        quiz = Quiz.objects.create(
            video=video,
            start_time=start_time,
            pass_mark=pass_mark,
        )

        question_text = request.POST.get('question_text')
        question = Question.objects.create(
            quiz=quiz,
            text=question_text,
        )

        answer1_text = request.POST.get('answer1_text')
        answer1_is_correct = request.POST.get('answer1_is_correct') == 'on'
        answer1 = Answer.objects.create(
            question=question,
            text=answer1_text,
            is_correct=answer1_is_correct,
        )

        answer2_text = request.POST.get('answer2_text')
        answer2_is_correct = request.POST.get('answer2_is_correct') == 'on'
        answer2 = Answer.objects.create(
            question=question,
            text=answer2_text,
            is_correct=answer2_is_correct,
        )

        answer3_text = request.POST.get('answer3_text')
        answer3_is_correct = request.POST.get('answer3_is_correct') == 'on'
        answer3 = Answer.objects.create(
            question=question,
            text=answer3_text,
            is_correct=answer3_is_correct,
        )

        answer4_text = request.POST.get('answer4_text')
        answer4_is_correct = request.POST.get('answer4_is_correct') == 'on'
        answer4 = Answer.objects.create(
            question=question,
            text=answer4_text,
            is_correct=answer4_is_correct,
        )
        return redirect('quiz_detail', quiz_id=quiz.id)

    return render(request, 'website/create_quiz.html', {'video': video})

def update_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    if request.method == 'POST':
        quiz.video_id = request.POST.get('video')
        quiz.start_time = request.POST.get('timestamp')
        quiz.pass_mark = request.POST.get('pass_mark')

        quiz.questions.all().delete()

        for i in range(1, 6):
            question_text = request.POST.get(f'question_{i}')
            if not question_text:
                continue

            question = Question.objects.create(quiz=quiz, text=question_text)

            answer1_text = request.POST.get(f'question_{i}_answer_1')
            answer1_correct = request.POST.get(f'question_{i}_answer_1_correct') == 'on'
            Answer.objects.create(question=question, text=answer1_text, is_correct=answer1_correct)

            answer2_text = request.POST.get(f'question_{i}_answer_2')
            answer2_correct = request.POST.get(f'question_{i}_answer_2_correct') == 'on'
            Answer.objects.create(question=question, text=answer2_text, is_correct=answer2_correct)

            answer3_text = request.POST.get(f'question_{i}_answer_3')
            answer3_correct = request.POST.get(f'question_{i}_answer_3_correct') == 'on'
            Answer.objects.create(question=question, text=answer3_text, is_correct=answer3_correct)

            answer4_text = request.POST.get(f'question_{i}_answer_4')
            answer4_correct = request.POST.get(f'question_{i}_answer_4_correct') == 'on'
            Answer.objects.create(question=question, text=answer4_text, is_correct=answer4_correct)

        quiz.save()

        return redirect('quiz-detail', quiz_id=quiz.id)

    return render(request, 'quiz/update_quiz.html', {'quiz': quiz})

def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    if request.method == 'POST':
        quiz.delete()
        return redirect('quiz_list')
    return render(request, 'website/delete_quiz.html', {'quiz': quiz})

import logging
logger = logging.getLogger(__name__)

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

def teacher_list(request):
    r_profile = get_object_or_404(Profile, user=request.user)
    organization = Organization.objects.filter(profile=r_profile)
    if organization.exists():
        organization = Organization.objects.get(profile=r_profile)
        teachers = Teacher.objects.filter(organization=organization)
        profiles = [teacher.profile for teacher in teachers]
        context = {'profiles': profiles}
        return render(request, 'website/teacher_list.html', context)
    else:
        return redirect('index')

def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not request.user.is_authenticated:
        # Store the course ID in session to redirect back after login
        request.session['enroll_after_login'] = course_id
        return redirect('login')
    
    # Check if user is already enrolled
    existing_enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
    if existing_enrollment:
        if existing_enrollment.status == 'cancelled':
            # Reactivate cancelled enrollment
            existing_enrollment.status = 'active'
            existing_enrollment.enrollment_date = timezone.now()
            existing_enrollment.save()
            messages.success(request, f"تم إعادة تفعيل اشتراكك في الدورة: {course.name}")
        else:
            messages.warning(request, f"أنت مسجل بالفعل في الدورة: {course.name}")
        return redirect(reverse('courseviewpage', args=[course_id]))
    
    # For free courses or if payment is handled elsewhere
    if request.method == 'POST':
        # Process enrollment
        enrollment = Enrollment.objects.create(
            course=course,
            student=request.user,
            status='active',
            enrollment_date=timezone.now()
        )
        
        # Send welcome email (optional)
        # send_enrollment_email(request.user.email, course)
        
        messages.success(request, f"تم تسجيلك بنجاح في الدورة: {course.name}")
        return redirect(reverse('courseviewpage', args=[course_id]))
    
    # Show enrollment confirmation page
    context = {
        'course': course,
    }
    return render(request, 'website/enrollment_confirmation.html', context)

@login_required
@require_POST
def mark_video_watched(request, video_id):
    """API endpoint to mark a video as watched"""
    try:
        video = get_object_or_404(Video, id=video_id)
        
        # Get or create video progress
        video_progress, created = VideoProgress.objects.get_or_create(
            student=request.user,
            video=video,
            defaults={'watched': True}
        )
        
        if not video_progress.watched:
            video_progress.watched = True
            video_progress.save()
        
        # Update enrollment progress
        enrollment = Enrollment.objects.filter(
            course=video.module.course,
            student=request.user
        ).first()
        
        if enrollment:
            from .utils import update_enrollment_progress
            progress = update_enrollment_progress(enrollment)
        else:
            progress = 0
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل مشاهدة الفيديو',
            'progress': progress
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def mark_content_viewed(request, content_type, content_id):
    """API endpoint to mark any content as viewed"""
    try:
        from .utils import mark_content_completed
        course = None
        
        # Get the course based on content type
        if content_type == 'video':
            video = get_object_or_404(Video, id=content_id)
            course = video.module.course
            
        elif content_type == 'note':
            # Handle both regular notes and module PDFs
            if content_id.startswith('module_pdf_'):
                module_id = content_id.replace('module_pdf_', '')
                module = get_object_or_404(Module, id=module_id)
                course = module.course
            elif content_id.startswith('additional_materials_'):
                module_id = content_id.replace('additional_materials_', '')
                module = get_object_or_404(Module, id=module_id)
                course = module.course
            else:
                note = get_object_or_404(Notes, id=content_id)
                course = note.module.course
            
        elif content_type == 'quiz':
            quiz = get_object_or_404(Quiz, id=content_id)
            course = quiz.course
            
        elif content_type == 'assignment':
            assignment = get_object_or_404(Assignment, id=content_id)
            course = assignment.course
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'نوع المحتوى غير صالح'
            }, status=400)
        
        # Check if user is enrolled
        if not Enrollment.objects.filter(course=course, student=request.user).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'غير مسجل في هذه الدورة'
            }, status=403)
        
        # Mark content as completed and get updated progress
        progress = mark_content_completed(request.user, course, content_type, content_id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل المشاهدة بنجاح',
            'progress': progress,
            'content_type': content_type,
            'content_id': content_id
        })
        
    except Exception as e:
        logger.error(f"Error in mark_content_viewed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)

@login_required
@require_POST
def submit_quiz(request):
    """Handle quiz submission"""
    try:
        quiz_id = request.POST.get('quiz_id')
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Calculate score
        total_questions = quiz.question_set.count()
        correct_answers = 0
        
        for question in quiz.question_set.all():
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        correct_answers += 1
                except Answer.DoesNotExist:
                    pass
        
        # Calculate percentage
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Check if passed
        pass_mark = getattr(quiz, 'pass_mark', 60)
        passed = score_percentage >= pass_mark
        
        # Save exam attempt
        try:
            UserExamAttempt.objects.create(
                user=request.user,
                exam=quiz,
                score=score_percentage,
                passed=passed
            )
        except Exception:
            pass
        
        # Update progress if passed
        if passed:
            enrollment = Enrollment.objects.filter(
                course=quiz.course,
                student=request.user
            ).first()
            
            if enrollment:
                from .utils import update_enrollment_progress
                progress = update_enrollment_progress(enrollment)
        
        # Redirect to results page or back to course
        if passed:
            messages.success(request, f'تهانينا! لقد نجحت في الاختبار بدرجة {score_percentage:.1f}%')
        else:
            messages.warning(request, f'لم تنجح في الاختبار. حصلت على {score_percentage:.1f}% والمطلوب {pass_mark}%')
        
        return redirect('courseviewpage', course_id=quiz.course.id)
        
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تسليم الاختبار: {str(e)}')
        return redirect('courseviewpage', course_id=quiz.course.id)

@login_required
@require_POST
def mark_assignment_completed(request, assignment_id):
    """API endpoint to mark an assignment as completed"""
    try:
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Create or update assignment submission
        submission, created = AssignmentSubmission.objects.get_or_create(
            user=request.user,
            assignment=assignment,
            defaults={
                'status': 'submitted',
                'submitted_at': timezone.now()
            }
        )
        
        # Update enrollment progress
        enrollment = Enrollment.objects.filter(
            course=assignment.course,
            student=request.user
        ).first()
        
        if enrollment:
            from .utils import update_enrollment_progress
            progress = update_enrollment_progress(enrollment)
        else:
            progress = 0
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل تسليم الواجب',
            'progress': progress
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def analytics(request):
    return render(request, 'website/analytics.html')

@login_required
def delete_pdf(request, course_id, pdf_type):
    """Delete a PDF file from a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is authorized to modify this course
    if not request.user.is_staff and (not hasattr(request.user, 'teacher') or request.user.teacher != course.teacher):
        messages.error(request, 'ليس لديك صلاحية لحذف هذا الملف')
        return redirect('update_course', course_id=course_id)
    
    # Delete the appropriate file based on pdf_type
    if pdf_type == 'syllabus_pdf' and course.syllabus_pdf:
        # Delete the file
        course.syllabus_pdf.delete(save=False)
        course.syllabus_pdf = None
        course.save()
        messages.success(request, 'تم حذف ملف المنهج بنجاح')
    elif pdf_type == 'materials_pdf' and course.materials_pdf:
        # Delete the file
        course.materials_pdf.delete(save=False)
        course.materials_pdf = None
        course.save()
        messages.success(request, 'تم حذف ملف المواد بنجاح')
    else:
        messages.error(request, 'لم يتم العثور على الملف المطلوب')
    
    # Redirect back to the update course page
    return redirect('update_course', course_id=course_id)

@login_required
def delete_module_pdf(request, module_id, pdf_type):
    """Delete a PDF file from a module"""
    module = get_object_or_404(Module, id=module_id)
    
    # Check if user is authorized to modify this module
    if not request.user.is_staff and (not hasattr(request.user, 'teacher') or request.user.teacher != module.course.teacher):
        messages.error(request, 'ليس لديك صلاحية لحذف هذا الملف')
        return redirect('update_course', course_id=module.course.id)
    
    # Delete the appropriate file based on pdf_type
    if pdf_type == 'module_pdf' and hasattr(module, 'module_pdf') and module.module_pdf:
        # Delete the file
        module.module_pdf.delete(save=False)
        module.module_pdf = None
        module.save()
        messages.success(request, 'تم حذف ملف PDF الرئيسي للموديول بنجاح')
    elif pdf_type == 'additional_materials' and hasattr(module, 'additional_materials') and module.additional_materials:
        # Delete the file
        module.additional_materials.delete(save=False)
        module.additional_materials = None
        module.save()
        messages.success(request, 'تم حذف ملف المواد الإضافية بنجاح')
    else:
        messages.error(request, 'لم يتم العثور على الملف المطلوب')
    
    # Redirect back to the update course page
    return redirect('update_course', course_id=module.course.id)

def ensure_course_has_module(course):
    """Ensure that a course has at least one module. Create one if none exists."""
    if not course.module_set.exists():
        # Create a default module
        module = Module.objects.create(
            course=course,
            name="الموديول الأول",
            description="الموديول الأساسي للدورة",
            number=1
        )
        logger.info(f"Created default module {module.id} for course {course.id}")
        return module
    return course.module_set.first()

def ensure_module_has_quiz(module, quiz_title="اختبار الموديول"):
    """Ensure that a module has a quiz. Create one if none exists and quiz is requested."""
    quiz = module.module_quizzes.first()
    if not quiz:
        quiz = Quiz.objects.create(
            title=quiz_title,
            description=f"اختبار للموديول: {module.name}",
            module=module,
            course=module.course,
            quiz_type='module',
            pass_mark=50.0,
            time_limit=10,
            is_active=True
        )
        logger.info(f"Created default quiz {quiz.id} for module {module.id}")
    return quiz

def course_category(request, category_slug):
    """
    View to display all content belonging to a specific category (courses and articles)
    """
    # Get the category or return 404 if not found
    category = get_object_or_404(Category, name=category_slug)
    
    # Get all courses in this category
    courses = Course.objects.filter(category=category, status='published')
    
    # Get all articles in this category
    articles = Article.objects.filter(category=category, status='published')
    
    context = {
        'category': category,
        'courses': courses,
        'articles': articles,
    }
    
    return render(request, 'website/category_courses.html', context)

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
        messages.success(request, 'تم إضافة التعليق بنجاح')
        return redirect('courseviewpage', course_id=course_id)
    
    messages.error(request, 'نص التعليق مطلوب')
    return redirect('courseviewpage', course_id=course_id)

def complete_course(request, course_id):
    """
    API endpoint to mark a course as completed
    Forces completion when student has sufficient progress
    """
    if request.method == 'POST':
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
                from .utils import update_enrollment_progress
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
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
@require_POST
def recalculate_progress(request, course_id):
    """API endpoint to recalculate course progress"""
    try:
        course = get_object_or_404(Course, id=course_id)
        enrollment = get_object_or_404(Enrollment, course=course, student=request.user)
        
        from .utils import update_enrollment_progress
        progress = update_enrollment_progress(enrollment)
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم إعادة حساب التقدم بنجاح',
            'progress': progress
        })
        
    except Exception as e:
        logger.error(f"Error recalculating progress: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)