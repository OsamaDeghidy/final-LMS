from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.db.models import Avg

from .models import (
    Category, Course, Module, Tags, Quiz, Question, Answer, Enrollment, 
    CourseReview, ReviewReply, UserProgress, ModuleProgress, CourseProgress,
    Assignment, AssignmentSubmission, UserExamAttempt, UserExamAnswer, 
    Exam, ExamQuestion, ExamAnswer, Attendance, QuizAttempt, QuizUserAnswer,
    Meeting, Participant, Notification, BookCategory, Review, Book, Article,
    Cart, CartItem, ContentProgress, Certification, Attachment
)
from user.models import Profile, Student, Organization, Teacher
from .utils import searchCourses

# Import course-related views
from .views_course import (
    allcourses, course_detail, update_course, delete_course, course, courseviewpage, 
    courseviewpagevideo, courseviewpagenote, create_module, update_module, 
                           delete_module, course_modules, quiz_list, view_quiz, create_quiz, update_quiz, 
                           delete_quiz, enroll_course, mark_video_watched, mark_content_viewed, 
                           mark_assignment_completed, delete_pdf, delete_module_pdf, add_to_cart, 
                           view_cart, remove_from_cart, checkout, submit_quiz, complete_course, 
                           recalculate_progress, course_category, add_comment, add_rating, generate_certificate,
                           download_certificate, course_statistics, search_courses, course_recommendations,
                           add_to_wishlist, remove_from_wishlist, view_wishlist)

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
    
    if profile.status in ['Teacher', 'Admin']:
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
        'courses': teacher_courses if profile.status in ['Teacher', 'Admin'] else [],
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

def contact(request):   
    return render(request, 'website/contact.html')

# courseviewpagenote function has been moved to views_course.py

# add_to_cart function has been moved to views_course.py
# view_cart function has been moved to views_course.py
# remove_from_cart function has been moved to views_course.py
# checkout function has been moved to views_course.py

# courseviewpage function has been moved to views_course.py

# courseviewpagevideo function has been moved to views_course.py

# submit_quiz function has been moved to views_course.py

# courseviewpagenote function has been moved to views_course.py

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
                    'course__module_set'
                )
                
                # Calculate progress for each enrollment
                for enrollment in enrollments:
                    # Calculate total videos in course
                    total_videos = sum(1 for module in enrollment.course.module_set.all() if module.video)
                    
                    if total_videos > 0:
                        # Get watched videos for this course
                        watched_videos = ModuleProgress.objects.filter(
                            user=request.user,
                            module__course=enrollment.course,
                            video_watched=True
                        ).count()
                        
                        # Calculate progress percentage
                        progress = (watched_videos / total_videos) * 100 if total_videos > 0 else 0
                    else:
                        progress = 0
                        
                    # Update enrollment progress
                    enrollment.progress = progress
                    enrollment.save(update_fields=['progress'])
                    
                    # Set completed flag
                    enrollment.completed = progress == 100
            
            # Query all courses to display in the dashboard (for teachers/admins)
            courses = Course.objects.all()
            
            # Get upcoming meetings for the user
            from django.utils import timezone
            from .models import Meeting, Participant
            
            # Get meetings where user is creator or participant
            created_meetings = Meeting.objects.filter(creator=request.user, start_time__gte=timezone.now())
            participating_meetings = Meeting.objects.filter(participant__user=request.user, start_time__gte=timezone.now())
            
            # Combine and remove duplicates
            upcoming_meetings = (created_meetings | participating_meetings).distinct().order_by('start_time')[:3]
            upcoming_meetings_count = (created_meetings | participating_meetings).distinct().count()
            
            context = {
                "profile": profile,
                "courses": courses,
                "enrollments": enrollments,
                "upcoming_meetings": upcoming_meetings,
                "upcoming_meetings_count": upcoming_meetings_count
            }
            return render(request, 'website/dashboard.html', context)
        except Profile.DoesNotExist:
            return HttpResponse('Profile does not exist for the user.')
        except Profile.MultipleObjectsReturned:
            return HttpResponse('Multiple profiles found for the user. Please contact support.')

# create_course function has been moved to views_course.py

# course_detail function has been moved to views_course.py

# update_course function has been moved to views_course.py

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
            data = json.loads(request.body)
            course_id = data.get('course_id')
            
            if not course_id:
                return JsonResponse({'error': 'Course ID is required'}, status=400)
                
            course = get_object_or_404(Course, id=course_id)
            
            # Check if user has permission to delete this course (teacher or admin)
            is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
            is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
            
            if not (is_teacher and hasattr(course, 'teacher') and course.teacher.profile == request.user.profile) and not (is_admin or request.user.is_superuser):
                if request.content_type == 'application/json':
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                else:
                    return redirect('course_detail', course_id=course_id)
            
            course.delete()
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': 'Course deleted successfully'})
            else:
                return redirect('dashboard')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

# course function has been moved to views_course.py

# create_module function has been moved to views_course.py

# update_module function has been moved to views_course.py

# delete_module function has been moved to views_course.py

# course_modules function has been moved to views_course.py

# quiz_list function has been moved to views_course.py

# view_quiz function has been moved to views_course.py

from datetime import datetime, timedelta

def create_quiz(request, video_id):
    video = Video.objects.get(id=video_id)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == video.module.course.teacher.profile) and not (is_admin or request.user.is_superuser):
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

# ensure_course_has_module function has been moved to views_course.py

# ensure_module_has_quiz function has been moved to views_course.py

# course_category function has been moved to views_course.py

# add_comment function has been moved to views_course.py

# complete_course function has been moved to views_course.py

# recalculate_progress function has been moved to views_course.py