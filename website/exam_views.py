from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from django.db import models
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator

from .models import (
    Course, Module, Exam, ExamQuestion, ExamAnswer, 
    UserExamAttempt, UserExamAnswer, Enrollment, Teacher, Student
)
from .utils_course import update_enrollment_progress

# Teacher Views - Exam Management

import logging
logger = logging.getLogger(__name__)

@login_required
def teacher_exams(request, course_id=None):
    """
    View for teachers to see exams
    If course_id is provided, shows exams for that course
    Otherwise shows a course selection page
    """
    logger.info(f"teacher_exams view called with course_id: {course_id}")
    
    # Check if user is a teacher or admin via their profile
    if not hasattr(request.user, 'profile') or (request.user.profile.status not in ['Teacher', 'Admin'] and not request.user.is_superuser):
        logger.warning(f"User {request.user} is not authorized to access teacher exams")
        return HttpResponseForbidden("You must be a teacher or admin to access this page.")
    
    # Get the teacher's profile
    teacher_profile = request.user.profile
    logger.info(f"Teacher profile found: {teacher_profile}")
    
    try:
        # Get the teacher object associated with the profile
        teacher = Teacher.objects.get(profile=teacher_profile)
        logger.info(f"Teacher object found: {teacher}")
        
        # Get all courses - all courses for admin, only taught courses for teachers
        if teacher_profile.status == 'Admin' or request.user.is_superuser:
            teacher_courses = Course.objects.all().order_by('name')
        else:
            teacher_courses = Course.objects.filter(teacher=teacher).order_by('name')
        logger.info(f"Found {teacher_courses.count()} courses")
        
        # Only get course and exams if course_id is provided
        course = None
        exams = []
        if course_id:
            logger.info(f"Looking for course with id {course_id}")
            if teacher_profile.status == 'Admin' or request.user.is_superuser:
                course = get_object_or_404(Course, id=course_id)
            else:
                course = get_object_or_404(Course, id=course_id, teacher=teacher)
            logger.info(f"Found course: {course}")
            exams = Exam.objects.filter(course=course).order_by('-created_at')
            logger.info(f"Found {exams.count()} exams for course {course_id}")
            
    except Teacher.DoesNotExist:
        # If no teacher object exists, show no courses
        logger.warning("No Teacher object found for this profile")
        teacher_courses = Course.objects.none()
        course = None
        exams = []
    
    context = {
        'course': course,
        'exams': exams,
        'teacher_courses': teacher_courses,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    logger.info(f"Rendering template with context: {context}")
    return render(request, 'website/exams/teacher_exams.html', context)

@login_required
def create_exam(request, course_id):
    """View for teachers/admins to create a new exam"""
    # Get the course
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the teacher or an admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and course.teacher.profile.user == request.user) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to create exams for this course.")
        
    modules = Module.objects.filter(course=course)
    
    # Prepare context with user profile and student data
    context = {
        'course': course,
        'modules': modules,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        module_id = request.POST.get('module')
        time_limit = request.POST.get('time_limit')
        pass_mark = request.POST.get('pass_mark')
        is_final = request.POST.get('is_final') == 'on'
        total_points = request.POST.get('total_points')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        allow_multiple_attempts = request.POST.get('allow_multiple_attempts') == 'on'
        max_attempts = request.POST.get('max_attempts')
        show_answers_after = request.POST.get('show_answers_after') == 'on'
        randomize_questions = request.POST.get('randomize_questions') == 'on'
        
        # Create the exam
        module = None
        if module_id:
            module = get_object_or_404(Module, id=module_id)
            
        exam = Exam.objects.create(
            course=course,
            title=title,
            description=description,
            module=module,
            time_limit=time_limit,
            pass_mark=pass_mark,
            is_final=is_final,
            total_points=total_points,
            start_date=start_date,
            end_date=end_date,
            allow_multiple_attempts=allow_multiple_attempts,
            max_attempts=max_attempts,
            show_answers_after=show_answers_after,
            randomize_questions=randomize_questions
        )
        
        messages.success(request, 'تم إنشاء الاختبار بنجاح')
        return redirect('add_question', exam_id=exam.id)
    
    # For GET requests, render the form with the prepared context
    return render(request, 'website/exams/create_exam.html', context)

@login_required
def edit_exam(request, exam_id):
    """View for teachers/admins to edit an existing exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user is the teacher or an admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and exam.course.teacher.profile.user == request.user) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to edit this exam.")
        
    modules = Module.objects.filter(course=exam.course)
    questions = ExamQuestion.objects.filter(exam=exam).order_by('order')
    
    # Prepare context with user profile and student data
    context = {
        'exam': exam,
        'modules': modules,
        'questions': questions,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    
    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.description = request.POST.get('description')
        
        module_id = request.POST.get('module')
        if module_id:
            exam.module = get_object_or_404(Module, id=module_id)
        else:
            exam.module = None
            
        exam.time_limit = request.POST.get('time_limit')
        exam.pass_mark = request.POST.get('pass_mark')
        exam.is_final = request.POST.get('is_final') == 'on'
        exam.total_points = request.POST.get('total_points')
        
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        exam.start_date = start_date if start_date else None
        exam.end_date = end_date if end_date else None
        
        exam.allow_multiple_attempts = request.POST.get('allow_multiple_attempts') == 'on'
        exam.max_attempts = request.POST.get('max_attempts')
        exam.show_answers_after = request.POST.get('show_answers_after') == 'on'
        exam.randomize_questions = request.POST.get('randomize_questions') == 'on'
        
        exam.save()
        messages.success(request, 'تم تحديث الاختبار بنجاح.')
        return redirect('teacher_exams_course', course_id=exam.course.id)
    
    return render(request, 'website/exams/edit_exam.html', context)

@login_required
def delete_exam(request, exam_id):
    """View for teachers/admins to delete an exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user is the teacher or an admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and exam.course.teacher.profile.user == request.user) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to delete this exam.")
    
    course_id = exam.course.id
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'تم حذف الامتحان بنجاح')
        return redirect('teacher_exams_course', course_id=course_id)
    
    context = {
        'exam': exam,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/delete_exam_confirm.html', context)

# Question Management Views

@login_required
def add_question(request, exam_id):
    """View for teachers to add a question to an exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("ليس لديك صلاحية إضافة أسئلة لهذا الاختبار")
    
    # Prepare context with user profile and student data
    context = {
        'exam': exam,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    
    if request.method == 'POST':
        text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        points = request.POST.get('points', 1)
        explanation = request.POST.get('explanation')
        
        # Get the highest order value and add 1
        highest_order = ExamQuestion.objects.filter(exam=exam).aggregate(max_order=models.Max('order'))['max_order'] or 0
        
        # Create the question
        question = ExamQuestion.objects.create(
            exam=exam,
            text=text,
            question_type=question_type,
            points=points,
            explanation=explanation,
            order=highest_order + 1
        )
        
        # Handle image upload if provided
        if 'image' in request.FILES:
            question.image = request.FILES['image']
            question.save()
        
        # For multiple choice and true/false questions, create answers
        if question_type in ['multiple_choice', 'true_false']:
            # For true/false questions
            if question_type == 'true_false':
                correct_answer = request.POST.get('true_false_answer')
                logger.info(f"Creating True/False question - correct_answer: {correct_answer}")
                
                # Create True answer
                ExamAnswer.objects.create(
                    question=question,
                    text='صحيح',
                    is_correct=correct_answer == 'true',
                    order=1
                )
                
                # Create False answer
                ExamAnswer.objects.create(
                    question=question,
                    text='خطأ',
                    is_correct=correct_answer == 'false',
                    order=2
                )
            else:  # For multiple choice questions
                # Get answer texts from the form
                answer_texts = request.POST.getlist('answer_text[]')
                correct_answer_index = request.POST.get('correct_answer')
                
                for i, answer_text in enumerate(answer_texts):
                    if not answer_text.strip():  # Skip empty answers
                        continue
                        
                    is_correct = str(i) == correct_answer_index
                    
                    ExamAnswer.objects.create(
                        question=question,
                        text=answer_text.strip(),
                        is_correct=is_correct,
                        order=i + 1
                    )
        
        messages.success(request, 'تم إضافة السؤال بنجاح.')
        return redirect('edit_exam', exam_id=exam.id)
    
    return render(request, 'website/exams/add_question.html', context)

@login_required
def edit_question(request, question_id):
    """View for teachers to edit a question"""
    question = get_object_or_404(ExamQuestion, id=question_id)
    exam = question.exam
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("ليس لديك صلاحية تعديل هذا السؤال")
    
    # Get existing answers
    answers = ExamAnswer.objects.filter(question=question).order_by('order')
    
    if request.method == 'POST':
        # Debug: Log the POST data
        logger.info(f"POST data for question {question.id}: {dict(request.POST)}")
        
        question.text = request.POST.get('text')
        question.points = request.POST.get('points', 1)
        question.explanation = request.POST.get('explanation')
        
        # Handle image upload if provided
        if 'image' in request.FILES:
            question.image = request.FILES['image']
        elif request.POST.get('remove_image') == 'on':
            question.image = None
        
        question.save()
        
        # Handle answers based on question type
        if question.question_type in ['multiple_choice', 'true_false']:
            if question.question_type == 'true_false':
                # Update true/false answers
                correct_answer = request.POST.get('true_false_answer')
                logger.info(f"True/False question - correct_answer: {correct_answer}")
                logger.info(f"Existing answers: {[(a.id, a.text, a.is_correct) for a in answers]}")
                
                # Check if we have the required True/False answers
                true_answer = None
                false_answer = None
                
                for answer in answers:
                    if answer.text in ['صحيح', 'True', 'صح']:
                        true_answer = answer
                    elif answer.text in ['خطأ', 'False']:
                        false_answer = answer
                
                # If we don't have the required answers, create them
                if not true_answer:
                    true_answer = ExamAnswer.objects.create(
                        question=question,
                        text='صحيح',
                        is_correct=correct_answer == 'true',
                        order=1
                    )
                    logger.info(f"Created true answer: {true_answer.id}")
                else:
                    true_answer.is_correct = correct_answer == 'true'
                    true_answer.save()
                    logger.info(f"Updated true answer: {true_answer.id} -> {true_answer.is_correct}")
                
                if not false_answer:
                    false_answer = ExamAnswer.objects.create(
                        question=question,
                        text='خطأ',
                        is_correct=correct_answer == 'false',
                        order=2
                    )
                    logger.info(f"Created false answer: {false_answer.id}")
                else:
                    false_answer.is_correct = correct_answer == 'false'
                    false_answer.save()
                    logger.info(f"Updated false answer: {false_answer.id} -> {false_answer.is_correct}")
                
                # Delete any extra answers that don't belong to True/False
                for answer in answers:
                    if answer.text not in ['صحيح', 'True', 'صح', 'خطأ', 'False']:
                        logger.info(f"Deleting extra answer: {answer.id} - {answer.text}")
                        answer.delete()
            else:  # multiple choice
                # Get existing answers to update
                existing_answers = {str(a.id): a for a in answers}
                
                # Get answer texts and IDs from the form
                answer_texts = request.POST.getlist('answer_text[]')
                answer_ids = request.POST.getlist('answer_id[]')
                correct_answer_index = request.POST.get('correct_answer')
                
                # Debug logging
                logger.info(f"Answer texts: {answer_texts}")
                logger.info(f"Answer IDs: {answer_ids}")
                logger.info(f"Correct answer index: {correct_answer_index}")
                logger.info(f"Existing answers: {list(existing_answers.keys())}")
                
                # Track which answers were updated
                updated_answers = set()
                
                # Process each answer
                for i, answer_text in enumerate(answer_texts):
                    if not answer_text.strip():  # Skip empty answers
                        continue
                        
                    is_correct = str(i) == correct_answer_index
                    
                    # Check if this is an existing answer
                    if i < len(answer_ids) and answer_ids[i] and answer_ids[i] in existing_answers:
                        # Update existing answer
                        answer = existing_answers[answer_ids[i]]
                        answer.text = answer_text.strip()
                        answer.is_correct = is_correct
                        answer.order = i + 1
                        answer.save()
                        updated_answers.add(answer_ids[i])
                    else:
                        # Create new answer
                        ExamAnswer.objects.create(
                            question=question,
                            text=answer_text.strip(),
                            is_correct=is_correct,
                            order=i + 1
                        )
                
                # Delete answers that weren't updated
                for answer_id, answer in existing_answers.items():
                    if answer_id not in updated_answers:
                        answer.delete()
        elif question.question_type == 'short_answer':
            # Handle model answer for short answer questions
            model_answer = request.POST.get('model_answer', '').strip()
            
            # Delete existing answers first
            answers.delete()
            
            # Create new model answer if provided
            if model_answer:
                ExamAnswer.objects.create(
                    question=question,
                    text=model_answer,
                    is_correct=True,  # Model answer is always "correct"
                    order=1
                )
        
        messages.success(request, 'تم تحديث السؤال بنجاح.')
        return redirect('edit_exam', exam_id=exam.id)
    
    context = {
        'question': question,
        'exam': exam,
        'answers': answers,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/edit_question.html', context)

@login_required
def delete_question(request, question_id):
    """View for teachers to delete a question"""
    question = get_object_or_404(ExamQuestion, id=question_id)
    exam = question.exam
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("ليس لديك صلاحية حذف هذا السؤال")
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'تم حذف السؤال بنجاح.')
        return redirect('edit_exam', exam_id=exam.id)
    
    context = {
        'question': question,
        'exam': exam,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/delete_question_confirm.html', context)

@login_required
def reorder_questions(request, exam_id):
    """AJAX view for reordering questions"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        exam = get_object_or_404(Exam, id=exam_id)
        
        # Check if user is the course teacher or admin
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
        is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
        
        if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
            return JsonResponse({'status': 'error', 'message': 'ليس لديك صلاحية تعديل هذا الاختبار'}, status=403)
        
        # Get the new order from the request
        try:
            question_order = request.POST.getlist('question_order[]')
            
            # Update the order of each question
            for i, question_id in enumerate(question_order):
                question = get_object_or_404(ExamQuestion, id=question_id, exam=exam)
                question.order = i
                question.save()
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'طلب غير صحيح'}, status=400)

# Student Exam Views

@login_required
def student_exams_list(request):
    """
    View for students to see all their enrolled courses with available exams
    """
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Student':
        return HttpResponseForbidden("You must be a student to access this page.")
    
    # Get the student's enrolled courses that have exams
    enrolled_courses = Course.objects.filter(
        enrollments__student__profile__user=request.user,
        exams__isnull=False
    ).distinct()
    
    # Count available exams for each course
    courses_with_exam_count = []
    for course in enrolled_courses:
        exam_count = Exam.objects.filter(course=course, is_active=True).count()
        if exam_count > 0:
            courses_with_exam_count.append({
                'course': course,
                'exam_count': exam_count
            })
    
    context = {
        'courses': courses_with_exam_count,
        'profile': request.user.profile,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/student_exams_list.html', context)

@login_required
def student_exams(request, course_id):
    """View for students to see available exams for a course"""
    logger.info(f"student_exams view called by user: {request.user.username}")
    logger.info(f"User profile status: {request.user.profile.status if hasattr(request.user, 'profile') else 'No profile'}")
    
    # Check if user has a student profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Student':
        logger.warning(f"User {request.user.username} is not a student")
        return HttpResponseForbidden("You must be a student to access this page.")
        
    course = get_object_or_404(Course, id=course_id)
    logger.info(f"Course found: {course.name} (ID: {course.id})")
    
    # Check if student is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get all active exams for the course
    current_time = timezone.now()
    logger.info(f"Current time (UTC): {current_time}")
    logger.info(f"Current time (local): {timezone.localtime(current_time)}")
    
    exams = Exam.objects.filter(
        course=course,
        is_active=True
    ).order_by('module__number', 'created_at')
    
    # Get all user attempts for these exams at once for better performance
    user_attempts = UserExamAttempt.objects.filter(
        user=request.user, 
        exam__in=exams
    ).select_related('exam').order_by('-start_time')
    
    # Create a dictionary to store attempts by exam ID
    attempts_by_exam = {}
    for attempt in user_attempts:
        if attempt.exam_id not in attempts_by_exam:
            attempts_by_exam[attempt.exam_id] = []
        attempts_by_exam[attempt.exam_id].append(attempt)
    
    # Process each exam
    available_exams = []
    logger.info(f"Processing {exams.count()} exams for course {course.name}")
    
    for exam in exams:
        # Get attempts for this exam
        exam_attempts = attempts_by_exam.get(exam.id, [])
        attempt_count = len(exam_attempts)
        
        # Check if exam is available based on start/end dates
        is_available = True
        is_upcoming = False
        is_expired = False
        
        # Convert to timezone-aware datetime for comparison if needed
        if exam.start_date:
            # If start_date is naive, make it timezone-aware using the current timezone
            start_date = exam.start_date
            if timezone.is_naive(start_date):
                # Assume the naive datetime is in the local timezone
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            
            # If current time is before start time, exam is upcoming
            if current_time < start_date:
                is_available = False
                is_upcoming = True
        
        if exam.end_date:
            # If end_date is naive, make it timezone-aware using the current timezone
            end_date = exam.end_date
            if timezone.is_naive(end_date):
                # Assume the naive datetime is in the local timezone
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
            
            # If current time is after end time, exam is expired
            if current_time > end_date:
                is_available = False
                is_expired = True
        
        # Check if user can take the exam based on attempt limits
        can_take = is_available and attempt_count < exam.max_attempts
        

        
        # Get the best score if there are attempts
        best_score = None
        if exam_attempts:
            best_score = max((a.score for a in exam_attempts if a.score is not None), default=None)
        
        # Calculate remaining attempts
        remaining_attempts = exam.max_attempts - attempt_count if exam.allow_multiple_attempts else (1 - attempt_count)
        
        available_exams.append({
            'exam': exam,
            'is_available': is_available,
            'is_upcoming': is_upcoming,
            'is_expired': is_expired,
            'can_take': can_take,
            'attempt_count': attempt_count,
            'remaining_attempts': max(0, remaining_attempts),
            'best_score': best_score,
            'passed': best_score >= exam.pass_mark if best_score is not None else False,
            'user_attempts': exam_attempts,
            'can_take_exam': can_take
        })
    
    # Separate upcoming exams for sidebar
    upcoming_exams = [exam_data for exam_data in available_exams if exam_data['is_upcoming']]
    
    context = {
        'course': course,
        'exams': available_exams,  # All exams including upcoming ones
        'upcoming_exams': upcoming_exams,  # Only upcoming exams for sidebar
        'profile': request.user.profile,
        'student': request.user.student if hasattr(request.user, 'student') else None,
        'now': timezone.now(),  # Add current time for template comparisons
        'now_local': timezone.localtime(timezone.now()),  # Local time for display
    }
    return render(request, 'website/exams/student_exams.html', context)

@login_required
def take_exam(request, exam_id):
    """View for students to take an exam"""
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    course = exam.course
    
    # Check if student is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Check if exam is available based on dates
    current_time = timezone.now()
    
    # Check start date
    if exam.start_date:
        start_date = exam.start_date
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        
        # If current time is before start time, exam hasn't started yet
        if current_time < start_date:
            local_start = timezone.localtime(start_date)
            messages.error(request, f'لم يبدأ وقت الاختبار بعد. سيبدأ في: {local_start.strftime("%Y-%m-%d %H:%M")}')
            return redirect('student_course_exams', course_id=course.id)
    
    # Check end date
    if exam.end_date:
        end_date = exam.end_date
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        
        # If current time is after end time, exam has expired
        if current_time > end_date:
            local_end = timezone.localtime(end_date)
            messages.error(request, f'انتهى وقت الاختبار. انتهى في: {local_end.strftime("%Y-%m-%d %H:%M")}')
            return redirect('student_course_exams', course_id=course.id)
    
    # Check attempt limits
    attempt_count = UserExamAttempt.objects.filter(user=request.user, exam=exam).count()
    if not exam.allow_multiple_attempts and attempt_count >= exam.max_attempts:
        messages.error(request, 'لقد وصلت إلى الحد الأقصى من المحاولات لهذا الاختبار.')
        return redirect('student_course_exams', course_id=course.id)
    
    # Create a new attempt
    attempt_number = attempt_count + 1
    attempt = UserExamAttempt.objects.create(
        user=request.user,
        exam=exam,
        attempt_number=attempt_number
    )
    
    # Get questions for the exam
    questions = ExamQuestion.objects.filter(exam=exam)
    if exam.randomize_questions:
        questions = questions.order_by('?')  # Randomize order
    else:
        questions = questions.order_by('order')
    
    # Calculate time left if there's a time limit
    time_left = None
    time_left_formatted = None
    if exam.time_limit:
        elapsed_time = (timezone.now() - attempt.start_time).total_seconds()
        time_left = max(0, exam.time_limit * 60 - elapsed_time)  # time_limit is in minutes
        
        # Format time left
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        seconds = int(time_left % 60)
        time_left_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'questions': questions,
        'time_limit': exam.time_limit,
        'time_left': time_left,
        'time_left_formatted': time_left_formatted,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/take_exam.html', context)

@login_required
def submit_exam(request, attempt_id):
    """View for students to submit their exam answers"""
    attempt = get_object_or_404(UserExamAttempt, id=attempt_id, user=request.user)
    exam = attempt.exam
    
    if request.method == 'POST':
        # Record end time
        attempt.end_time = timezone.now()
        
        # Process each question
        for question in exam.questions.all():
            answer_key = f'question_{question.id}'
            
            if question.question_type == 'multiple_choice' or question.question_type == 'true_false':
                # Get selected answer ID
                selected_answer_id = request.POST.get(answer_key)
                selected_answer = None
                is_correct = False
                points_earned = 0
                
                if selected_answer_id:
                    try:
                        selected_answer = ExamAnswer.objects.get(id=selected_answer_id, question=question)
                        is_correct = selected_answer.is_correct
                        points_earned = question.points if is_correct else 0
                    except ExamAnswer.DoesNotExist:
                        pass
                
                # Save the user's answer
                UserExamAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    points_earned=points_earned
                )
            
            elif question.question_type == 'short_answer':
                # Get text answer
                text_answer = request.POST.get(answer_key, '').strip()
                
                # For short answers, teacher will need to grade manually
                # We'll set is_correct to None for now
                UserExamAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=text_answer,
                    is_correct=None,
                    points_earned=0  # Will be updated when graded
                )
        
        # Calculate score for multiple choice and true/false questions
        attempt.calculate_score()
        
        # Update enrollment progress
        try:
            enrollment = Enrollment.objects.get(student=request.user, course=exam.course)
            update_enrollment_progress(enrollment)
        except Enrollment.DoesNotExist:
            pass
        
        return redirect('exam_results', attempt_id=attempt.id)
    
    # If not POST, redirect back to the exam
    return redirect('take_exam', exam_id=exam.id)

@login_required
def exam_results(request, attempt_id):
    """View for students to see their exam results"""
    attempt = get_object_or_404(UserExamAttempt, id=attempt_id, user=request.user)
    exam = attempt.exam
    
    # Get all answers for this attempt
    answers = UserExamAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_answer')
    
    # Organize answers by question type
    mc_tf_answers = []
    short_answers = []
    
    for answer in answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            mc_tf_answers.append(answer)
        else:  # short_answer
            short_answers.append(answer)
    
    # Check if we should show correct answers
    show_answers = exam.show_answers_after
    
    context = {
        'attempt': attempt,
        'exam': exam,
        'mc_tf_answers': mc_tf_answers,
        'short_answers': short_answers,
        'show_answers': show_answers,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/exam_results.html', context)

@login_required
def grade_short_answers(request, attempt_id):
    """View for teachers to grade short answer questions"""
    attempt = get_object_or_404(UserExamAttempt, id=attempt_id)
    exam = attempt.exam
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("ليس لديك صلاحية تقييم هذا الاختبار")
    
    # Get short answer questions
    short_answers = UserExamAnswer.objects.filter(
        attempt=attempt,
        question__question_type='short_answer'
    ).select_related('question')
    
    if request.method == 'POST':
        # Process each short answer
        for answer in short_answers:
            points_key = f'points_{answer.id}'
            is_correct_key = f'is_correct_{answer.id}'
            
            points = request.POST.get(points_key, 0)
            is_correct = request.POST.get(is_correct_key) == 'on'
            
            # Update the answer
            answer.points_earned = float(points) if points else 0
            answer.is_correct = is_correct
            answer.save()
        
        # Recalculate the attempt score
        attempt.calculate_score()
        
        messages.success(request, 'تم تقييم الإجابات بنجاح.')
        return redirect('teacher_exam_attempts', exam_id=exam.id)
    
    context = {
        'attempt': attempt,
        'exam': exam,
        'short_answers': short_answers,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/grade_short_answers.html', context)

@login_required
def teacher_exam_attempts(request, exam_id):
    """View for teachers to see all attempts for an exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user is the course teacher or admin
    is_teacher = hasattr(request.user, 'profile') and request.user.profile.status == 'Teacher'
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'Admin'
    
    if not (is_teacher and request.user.profile == exam.course.teacher.profile) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("ليس لديك صلاحية عرض محاولات هذا الاختبار")
    
    # Get all attempts for this exam
    attempts = UserExamAttempt.objects.filter(exam=exam).order_by('-start_time')
    
    # Check if there are any attempts with ungraded short answers
    ungraded_attempts = []
    for attempt in attempts:
        has_ungraded = UserExamAnswer.objects.filter(
            attempt=attempt,
            question__question_type='short_answer',
            is_correct=None
        ).exists()
        
        if has_ungraded:
            ungraded_attempts.append(attempt.id)
    
    context = {
        'exam': exam,
        'attempts': attempts,
        'ungraded_attempts': ungraded_attempts,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
        'student': request.user.student if hasattr(request.user, 'student') else None,
    }
    return render(request, 'website/exams/teacher_exam_attempts.html', context)
