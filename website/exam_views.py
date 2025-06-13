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
from .utils import update_enrollment_progress

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
    if not hasattr(request.user, 'profile') or (request.user.profile.status not in ['Teacher', 'admin'] and not request.user.is_superuser):
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
        if teacher_profile.status == 'admin' or request.user.is_superuser:
            teacher_courses = Course.objects.all().order_by('name')
        else:
            teacher_courses = Course.objects.filter(teacher=teacher).order_by('name')
        logger.info(f"Found {teacher_courses.count()} courses")
        
        # Only get course and exams if course_id is provided
        course = None
        exams = []
        if course_id:
            logger.info(f"Looking for course with id {course_id}")
            if teacher_profile.status == 'admin' or request.user.is_superuser:
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
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'admin'
    
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
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'admin'
    
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
    is_admin = hasattr(request.user, 'profile') and request.user.profile.status == 'admin'
    
    if not (is_teacher and exam.course.teacher.profile.user == request.user) and not (is_admin or request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to delete this exam.")
    
    course_id = exam.course.id
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'تم حذف الامتحان بنجاح')
        return redirect('teacher_exams', course_id=course_id)
    
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
    
    # Check if user is the course teacher through profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Teacher' or request.user.profile != exam.course.teacher.profile:
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
                # Create True answer
                ExamAnswer.objects.create(
                    question=question,
                    text='صح',
                    is_correct=request.POST.get('correct_answer') == 'true',
                    order=1
                )
                
                # Create False answer
                ExamAnswer.objects.create(
                    question=question,
                    text='خطأ',
                    is_correct=request.POST.get('correct_answer') == 'false',
                    order=2
                )
            else:  # For multiple choice questions
                # Get the number of answer options
                answer_count = int(request.POST.get('answer_count', 0))
                
                for i in range(1, answer_count + 1):
                    answer_text = request.POST.get(f'answer_{i}')
                    is_correct = request.POST.get(f'correct_answer') == str(i)
                    
                    if answer_text:  # Only create if text is provided
                        ExamAnswer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=is_correct,
                            order=i
                        )
        
        messages.success(request, 'تم إضافة السؤال بنجاح.')
        return redirect('edit_exam', exam_id=exam.id)
    
    return render(request, 'website/exams/add_question.html', context)

@login_required
def edit_question(request, question_id):
    """View for teachers to edit a question"""
    question = get_object_or_404(ExamQuestion, id=question_id)
    exam = question.exam
    
    # Check if user is the course teacher through profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Teacher' or request.user.profile != exam.course.teacher.profile:
        return HttpResponseForbidden("ليس لديك صلاحية تعديل هذا السؤال")
    
    # Get existing answers
    answers = ExamAnswer.objects.filter(question=question).order_by('order')
    
    if request.method == 'POST':
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
                correct_answer = request.POST.get('correct_answer')
                
                for answer in answers:
                    if answer.text == 'صح':
                        answer.is_correct = correct_answer == 'true'
                    else:  # 'خطأ'
                        answer.is_correct = correct_answer == 'false'
                    answer.save()
            else:  # multiple choice
                # Get existing answers to update
                existing_answers = {str(a.id): a for a in answers}
                
                # Get the number of answer options
                answer_count = int(request.POST.get('answer_count', 0))
                
                # Track which answers were updated
                updated_answers = set()
                
                for i in range(1, answer_count + 1):
                    answer_id = request.POST.get(f'answer_id_{i}')
                    answer_text = request.POST.get(f'answer_{i}')
                    is_correct = request.POST.get('correct_answer') == str(i)
                    
                    if answer_id and answer_id in existing_answers:  # Update existing
                        answer = existing_answers[answer_id]
                        answer.text = answer_text
                        answer.is_correct = is_correct
                        answer.order = i
                        answer.save()
                        updated_answers.add(answer_id)
                    elif answer_text:  # Create new
                        ExamAnswer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=is_correct,
                            order=i
                        )
                
                # Delete answers that weren't updated
                for answer_id, answer in existing_answers.items():
                    if answer_id not in updated_answers:
                        answer.delete()
        
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
    
    # Check if user is the course teacher through profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Teacher' or request.user.profile != exam.course.teacher.profile:
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
        
        # Check if user is the course teacher
        if request.user != exam.course.teacher:
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
    for exam in exams:
        # Get attempts for this exam
        exam_attempts = attempts_by_exam.get(exam.id, [])
        attempt_count = len(exam_attempts)
        
        # Check if exam is available based on start/end dates
        is_available = True
        if exam.start_date and exam.start_date > current_time:
            is_available = False
        if exam.end_date and exam.end_date < current_time:
            is_available = False
        
        # Check if user can take the exam based on attempt limits
        can_take = is_available and (exam.allow_multiple_attempts or attempt_count < exam.max_attempts)
        
        # Get the best score if there are attempts
        best_score = None
        if exam_attempts:
            best_score = max((a.score for a in exam_attempts if a.score is not None), default=None)
        
        available_exams.append({
            'exam': exam,
            'is_available': is_available,
            'can_take': can_take,
            'attempt_count': attempt_count,
            'best_score': best_score,
            'passed': best_score >= exam.pass_mark if best_score is not None else False,
            'user_attempts': exam_attempts,
            'can_take_exam': can_take
        })
    
    context = {
        'course': course,
        'exams': available_exams,  # Changed from available_exams to match template
        'profile': request.user.profile,
        'student': request.user,
        'now': timezone.now(),  # Add current time for template comparisons
    }
    return render(request, 'website/exams/student_exams.html', context)

@login_required
def take_exam(request, exam_id):
    """View for students to take an exam"""
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    course = exam.course
    
    # Check if student is enrolled
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    # Check if exam is available based on dates
    current_time = timezone.now()
    if exam.start_date and exam.start_date > current_time:
        messages.error(request, 'لم يبدأ وقت الاختبار بعد.')
        return redirect('student_exams', course_id=course.id)
    
    if exam.end_date and exam.end_date < current_time:
        messages.error(request, 'انتهى وقت الاختبار.')
        return redirect('student_exams', course_id=course.id)
    
    # Check attempt limits
    attempt_count = UserExamAttempt.objects.filter(user=request.user, exam=exam).count()
    if not exam.allow_multiple_attempts and attempt_count >= exam.max_attempts:
        messages.error(request, 'لقد وصلت إلى الحد الأقصى من المحاولات لهذا الاختبار.')
        return redirect('student_exams', course_id=course.id)
    
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
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'questions': questions,
        'time_limit': exam.time_limit,
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
        update_enrollment_progress(request.user, exam.course)
        
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
    
    # Check if user is the course teacher through profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Teacher' or request.user.profile != exam.course.teacher.profile:
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
    
    # Check if user is the course teacher through profile
    if not hasattr(request.user, 'profile') or request.user.profile.status != 'Teacher' or request.user.profile != exam.course.teacher.profile:
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
