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

from .models import Category, Course, Module, Video, Comment, SubComment, Notes, Tags, Quiz, Question, Answer, Enrollment, Review, VideoProgress, Cart, CartItem, Assignment, AssignmentSubmission, UserExamAttempt, ContentProgress, Article
from user.models import Profile, Student, Organization, Teacher
from .utils_course import searchCourses, update_enrollment_progress, mark_content_completed, get_completed_content_ids, get_user_course_progress, get_user_enrolled_courses, ensure_course_has_module

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
    
    # Get all articles in this category
    articles = Article.objects.filter(category=category, status='published')
    
    context = {
        'category': category,
        'courses': courses,
        'articles': articles,
    }
    
    return render(request, 'website/category_courses.html', context)

# Course detail and management views
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
    }
    
    return render(request, 'website/courses/course_detail.html', context)

@login_required
def course(request):
    courses = Course.objects.filter(teacher__profile__user=request.user)
    return render(request, 'website/course.html', {'courses': courses})

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
    
    # Get all modules for this course
    modules = Module.objects.filter(course=course).order_by('number')
    
    # Update last accessed time
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['last_accessed'])
    
    # Get completed content IDs for progress tracking
    completed_videos = get_completed_content_ids(request.user, course, 'video')
    completed_notes = get_completed_content_ids(request.user, course, 'note')
    completed_assignments = get_completed_content_ids(request.user, course, 'assignment')
    completed_quizzes = get_completed_content_ids(request.user, course, 'quiz')
    
    # Get completed PDF files (now properly tracking them)
    completed_pdfs = get_completed_content_ids(request.user, course, 'pdf')
    
    # Check if specific content is requested via URL parameters
    content_type = request.GET.get('content_type')
    content_id = request.GET.get('content_id')
    
    current_content = None
    next_content = None
    prev_content = None
    
    if content_type == 'module_pdf' and content_id:
        # Get the module with the PDF file
        try:
            module = Module.objects.get(id=content_id, course=course)
            if module.module_pdf:
                # Create content object for the module PDF
                current_content = {
                    'type': 'module_pdf',
                    'content': module,
                }
        except Module.DoesNotExist:
            messages.error(request, _('Module not found.'))
    
    context = {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'completed_videos': completed_videos,
        'completed_notes': completed_notes,
        'completed_assignments': completed_assignments,
        'completed_quizzes': completed_quizzes,
        'completed_pdfs': completed_pdfs,  # Now properly tracking PDF completion
        'current_content': current_content,
        'next_content': next_content,
        'prev_content': prev_content,
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
                # Check if profile is a teacher
                if request.user.profile.status != 'Teacher':
                    return JsonResponse({
                        'success': False,
                        'message': 'يجب أن تكون معلمًا لإنشاء دورة. يرجى التقديم كمعلم أولاً.'
                    })
                return JsonResponse({
                    'success': False,
                    'message': 'حدث خطأ في العثور على ملف المعلم الخاص بك. يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني.'
                })
            
            # Create course
            course = Course.objects.create(
                name=name,
                description=description,
                small_description=small_description,
                price=price,
                category=category,
                teacher=teacher,
                level=level
            )
            
            # Handle tags
            tags = request.POST.get('tags', '').split(',')
            for tag_name in tags:
                tag_name = tag_name.strip()
                if tag_name:
                    tag, created = Tags.objects.get_or_create(name=tag_name)
                    course.tags.add(tag)
            
            # Handle modules
            module_count = 0
            # Find the maximum module index from the form data
            for key in request.POST.keys():
                if key.startswith('module_') and key.endswith('_title'):
                    module_count += 1
            
            logger.info(f"Found {module_count} modules to process")
            
            for i in range(1, module_count + 1):
                module_title = request.POST.get(f'module_{i}_title')
                if not module_title:
                    continue
                    
                logger.info(f"Creating module {i}: {module_title}")
                module = Module.objects.create(
                    course=course,
                    name=module_title,
                    number=i
                )
                
                # Process PDFs for this module
                pdf_count = int(request.POST.get(f'module_{i}_pdf_count', 0))
                for pdf_idx in range(1, pdf_count + 1):
                    pdf_file = request.FILES.get(f'module_{i}_pdf_{pdf_idx}')
                    if pdf_file and pdf_file.name.lower().endswith('.pdf'):
                        module.module_pdf = pdf_file
                        module.save()
                        logger.info(f"Added PDF {pdf_file.name} to module {module_title}")
                
                # Process quiz for this module
                has_quiz = request.POST.get(f'module_{i}_has_quiz') == '1'
                if has_quiz:
                    question_count = int(request.POST.get(f'module_{i}_question_count', 0))
                    logger.info(f"Module {i} has quiz with {question_count} questions")
                    
                    for q in range(1, question_count + 1):
                        question_type = request.POST.get(f'module_{i}_question_{q}_type')
                        question_text = request.POST.get(f'module_{i}_question_{q}_text')
                        
                        if not question_text:
                            continue
                            
                        logger.info(f"Creating question {q} of type {question_type}")
                        question = Question.objects.create(
                            module=module,
                            question_type=question_type,
                            text=question_text,
                            order=q
                        )
                        
                        if question_type == 'multiple_choice':
                            answer_count = int(request.POST.get(f'module_{i}_question_{q}_answer_count', 0))
                            correct_answer = int(request.POST.get(f'module_{i}_question_{q}_correct_answer', 1))
                            
                            for a in range(1, answer_count + 1):
                                answer_text = request.POST.get(f'module_{i}_question_{q}_answer_{a}')
                                if answer_text:
                                    is_correct = (a == correct_answer)
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_text,
                                        is_correct=is_correct
                                    )
                                    logger.info(f"Added answer: {answer_text} (correct: {is_correct})")
                        
                        elif question_type in ['true_false', 'short_answer']:
                            correct_answer = request.POST.get(f'module_{i}_question_{q}_correct_answer', '')
                            if correct_answer:
                                Answer.objects.create(
                                    question=question,
                                    text=correct_answer,
                                    is_correct=True
                                )
                                logger.info(f"Added {question_type} answer: {correct_answer}")
            
            messages.success(request, 'تم إنشاء الدورة بنجاح')
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
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
        messages.error(request, _('You do not have permission to edit this course.'))
        return redirect('course')
    
    if request.method == 'POST':
        # Process course update form
        # Implementation details omitted for brevity
        return redirect('course')
    else:
        # Display course update form
        return render(request, 'website/courses/update_course.html', {'course': course})

@login_required
def delete_course(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is the course teacher
        if request.user != course.teacher.profile.user:
            messages.error(request, _('You do not have permission to delete this course.'))
            return redirect('course')
        
        course.delete()
        messages.success(request, _('Course deleted successfully.'))
    
    return redirect('course')

# Module management views
@login_required
def create_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
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
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
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
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
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
    # Get the course based on content type and ID
    course = None
    
    if content_type == 'video':
        video = get_object_or_404(Video, id=content_id)
        course = video.module.course
    elif content_type == 'note':
        note = get_object_or_404(Notes, id=content_id)
        course = note.module.course
    elif content_type == 'assignment':
        assignment = get_object_or_404(Assignment, id=content_id)
        course = assignment.course
    elif content_type == 'quiz':
        quiz = get_object_or_404(Quiz, id=content_id)
        course = quiz.course
    elif content_type == 'pdf':
        # Handle different PDF types (module PDF, course PDF, etc)
        if content_id.startswith('module_pdf_'):
            module_id = content_id.replace('module_pdf_', '')
            module = get_object_or_404(Module, id=module_id)
            course = module.course
        elif content_id.startswith('course_syllabus_'):
            course_id = content_id.replace('course_syllabus_', '')
            course = get_object_or_404(Course, id=course_id)
        elif content_id.startswith('course_materials_'):
            course_id = content_id.replace('course_materials_', '')
            course = get_object_or_404(Course, id=course_id)
        else:
            # Try to handle as a module PDF directly
            try:
                module = get_object_or_404(Module, id=content_id)
                course = module.course
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': _('Invalid PDF content ID')
                }, status=400)
    else:
        return JsonResponse({
            'status': 'error',
            'message': _('Invalid content type')
        }, status=400)
    
    if not course:
        return JsonResponse({
            'status': 'error',
            'message': _('Could not determine course for this content')
        }, status=400)
        
    # Mark content as completed
    progress = mark_content_completed(request.user, course, content_type, content_id)
    
    return JsonResponse({
        'status': 'success',
        'message': _('Content marked as viewed'),
        'progress': progress
    })

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
    try:
        course = get_object_or_404(Course, id=course_id)
        enrollment = get_object_or_404(Enrollment, course=course, student=request.user)
        
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
            'message': f'\u062d\u062f\u062b \u062e\u0637\u0623: {str(e)}'
        }, status=500)

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
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
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
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
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
        data = json.loads(request.body)
        quiz_id = data.get('quiz_id')
        answers = data.get('answers', {})
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        course = quiz.course
        
        # Calculate score
        total_questions = quiz.question_set.count()
        correct_answers = 0
        
        for question_id, answer_id in answers.items():
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                selected_answer = Answer.objects.get(id=answer_id, question=question)
                
                if selected_answer.is_correct:
                    correct_answers += 1
            except (Question.DoesNotExist, Answer.DoesNotExist):
                pass
        
        if total_questions > 0:
            score = (correct_answers / total_questions) * 100
        else:
            score = 0
        
        # Check if passed
        passed = score >= quiz.passing_score
        
        # Record attempt
        attempt = UserExamAttempt.objects.create(
            user=request.user,
            exam=quiz,
            score=score,
            passed=passed
        )
        
        # If passed, mark as completed in ContentProgress
        if passed:
            mark_content_completed(request.user, course, 'quiz', quiz_id)
        
        # Update enrollment progress
        try:
            enrollment = Enrollment.objects.get(course=course, student=request.user)
            progress = update_enrollment_progress(enrollment)
        except Enrollment.DoesNotExist:
            progress = 0
        
        return JsonResponse({
            'status': 'success',
            'score': score,
            'passed': passed,
            'passing_score': quiz.passing_score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

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

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(course=course, student=request.user).exists():
        messages.info(request, _('You are already enrolled in this course.'))
        return redirect('courseviewpage', course_id=course_id)
    
    # Check if course is free or if user has purchased it
    if course.price == 0 or CartItem.objects.filter(cart__user=request.user, course=course, purchased=True).exists():
        # Create enrollment
        Enrollment.objects.create(
            course=course,
            student=request.user
        )
        messages.success(request, _('Successfully enrolled in the course.'))
        return redirect('courseviewpage', course_id=course_id)
    else:
        messages.error(request, _('You need to purchase this course before enrolling.'))
        return redirect('course_detail', course_id=course_id)


# File management
@login_required
def delete_pdf(request, course_id, pdf_type):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the course teacher
    if request.user != course.teacher.profile.user:
        messages.error(request, _('You do not have permission to delete files from this course.'))
        return redirect('course')
    
    if pdf_type == 'syllabus':
        if course.syllabus:
            course.syllabus.delete()
            course.syllabus = None
    elif pdf_type == 'requirements':
        if course.requirements_file:
            course.requirements_file.delete()
            course.requirements_file = None
    
    course.save()
    messages.success(request, _('File deleted successfully.'))
    return redirect('update_course', course_id=course_id)

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
@login_required
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

@login_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, purchased=False)
        total_price = sum(item.course.price for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total_price = 0
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    
    return render(request, 'website/cart.html', context)

@login_required
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

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart, purchased=False)
        
        if not cart_items.exists():
            messages.error(request, _('Your cart is empty.'))
            return redirect('view_cart')
        
        # Process payment (simplified for now)
        for item in cart_items:
            item.purchased = True
            item.purchase_date = timezone.now()
            item.save()
            
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
@login_required
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
    course = get_object_or_404(Course, id=course_id)
    
    try:
        enrollment = Enrollment.objects.get(course=course, student=request.user)
        
        # Check if course is completed
        if enrollment.progress < 100:
            messages.error(request, _('You must complete the course to receive a certificate.'))
            return redirect('courseviewpage', course_id=course_id)
        
        # Check if certificate already exists
        certificate, created = Certificate.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'date_issued': timezone.now(),
                'certificate_id': f'CERT-{course.id}-{request.user.id}-{int(time.time())}'
            }
        )
        
        # Render certificate template
        context = {
            'certificate': certificate,
            'course': course,
            'user': request.user,
            'date': certificate.date_issued.strftime('%B %d, %Y')
        }
        
        return render(request, 'website/certificate.html', context)
    
    except Enrollment.DoesNotExist:
        messages.error(request, _('You are not enrolled in this course.'))
        return redirect('courseviewpage', course_id=course_id)

@login_required
def download_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    course = certificate.course
    
    # Generate PDF certificate
    try:
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file"
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Draw certificate content
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height-100, "Certificate of Completion")
        
        p.setFont("Helvetica", 16)
        p.drawCentredString(width/2, height-150, f"This is to certify that")
        
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width/2, height-190, f"{request.user.get_full_name() or request.user.username}")
        
        p.setFont("Helvetica", 16)
        p.drawCentredString(width/2, height-230, "has successfully completed the course")
        
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width/2, height-270, f"{course.title}")
        
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height-320, f"Date: {certificate.date_issued.strftime('%B %d, %Y')}")
        p.drawCentredString(width/2, height-350, f"Certificate ID: {certificate.certificate_id}")
        
        # Draw border
        p.setStrokeColorRGB(0.7, 0.7, 0.9)
        p.setLineWidth(5)
        p.rect(50, 50, width-100, height-100)
        
        # Close the PDF object cleanly
        p.showPage()
        p.save()
        
        # Get the value of the BytesIO buffer and write it to the response
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{course.slug}.pdf"'
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating certificate PDF: {e}")
        messages.error(request, _('Error generating certificate. Please try again later.'))
        return redirect('courseviewpage', course_id=course.id)

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
