from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Course, Module, Video, Comment, SubComment, Notes,Monitor, Tags, Quiz, Question, Answer, Enrollment
from user.models import Profile, Student, Organization, Teacher
from datetime import datetime, timedelta
from django.contrib.gis.geoip2 import GeoIP2
from django_user_agents.utils import get_user_agent
import requests
import json
from django.urls import reverse
from .utils import searchCourses
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

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
    courses = Course.objects.all()
    context = {
        "courses": courses
    }
    courses, search_query = searchCourses(request)
    context = {'courses': courses,'search_query': search_query}
    return render(request, 'website/allcourses.html', context)

def contact(request):   
    return render(request, 'website/contact.html')

def courseviewpage(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
    if is_enrolled:
        return render(request, 'website/courseviewpage.html', {'course': course})
    else:
        return redirect('course_detail',course_id=course.id)

def courseviewpagevideo(request, course_id, video_id):
    course = get_object_or_404(Course, id=course_id)
    video = get_object_or_404(Video, id=video_id)
    is_enrolled = False
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
    if is_enrolled:
        quiz = Quiz.objects.filter(video=video).first()
        questions = quiz.question_set.all() if quiz else []
        return render(request, 'website/courseviewvideo.html', {'course': course, 'video': video, 'questions': questions, 'quiz': quiz})
    else:
        return redirect('course_detail', course_id=course.id)

def submit_quiz(request):
    if request.method == 'POST' and request.user.is_authenticated:
        # Get all submitted answers
        submitted_answers = {}
        for key, value in request.POST.items():
            # Parse question IDs from form data
            if key.startswith('question_'):
                question_id = key.split('_')[1]
                if question_id not in submitted_answers:
                    submitted_answers[question_id] = []
                submitted_answers[question_id].append(value)
        
        # Calculate score
        total_questions = 0
        correct_answers = 0
        
        for question_id, answer_ids in submitted_answers.items():
            try:
                question = Question.objects.get(id=question_id)
                total_questions += 1
                
                # Get correct answers for this question
                correct_answer_ids = [str(answer.id) for answer in question.answer_set.filter(is_correct=True)]
                
                # Check if submitted answers match correct answers
                if set(answer_ids) == set(correct_answer_ids):
                    correct_answers += 1
            except Question.DoesNotExist:
                continue
        
        # Calculate percentage score
        score = 0
        if total_questions > 0:
            score = (correct_answers / total_questions) * 100
        
        # Determine if passed based on quiz pass mark
        passed = False
        quiz_id = request.POST.get('quiz_id')
        if quiz_id:
            try:
                quiz = Quiz.objects.get(id=quiz_id)
                passed = score >= quiz.pass_mark
            except Quiz.DoesNotExist:
                pass
        
        # Return JSON response with results
        return JsonResponse({
            'score': score,
            'passed': passed,
            'correct_answers': correct_answers,
            'total_questions': total_questions
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def courseviewpagenote(request, course_id, note_id):
    course = get_object_or_404(Course, id=course_id)
    note = get_object_or_404(Notes, id=note_id)
    is_enrolled = False
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
    if is_enrolled:
        return render(request, 'website/courseviewnote.html', {'course': course, 'note': note})
    else:
        return redirect('course_detail', course_id=course.id)

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('index')  # Ensure 'index' is defined in URLs
    else:
        try:
            profile = Profile.objects.get(user=request.user)
            # Query all courses to display in the dashboard
            courses = Course.objects.all()
            context = {
                "profile": profile,
                "courses": courses
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
                course = Course(
                    name=name,
                    description=description,
                    image_course=image_course,
                    price=price,
                    small_description=small_description,
                    learned=learned,
                    teacher=teacher,
                    organization=teacher.organization,
                    created_at=datetime.today(),
                    updated_at=datetime.today()
                )
                course.save()
                course.tags.set(tags)
                return redirect('course_detail', course_id=course.id)
            except ObjectDoesNotExist:
                return HttpResponse("Error: Teacher matching query does not exist.", status=404)
        
        # Get the profile for the dashboard_base.html template
        profile = Profile.objects.get(user=request.user)
        context = {"profile": profile}
        return render(request, 'website/create_course.html', context)
    else:
        return redirect('index')

def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    monitor = None
    if request.user.is_authenticated:
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
        monitor.city = location['city']
        monitor.region = location['region']
        monitor.timeZone = location['time_zone']
        user_agent = get_user_agent(request)
        monitor.browser = user_agent.browser.family
        monitor.browser_version = user_agent.browser.version_string
        monitor.operating_system = user_agent.os.family
        monitor.device = user_agent.device.family
        monitor.language = request.headers.get('Accept-Language')
        monitor.screen_resolution = request.headers.get('X-Original-Request-Screen-Resolution')
        monitor.referrer = request.META.get('HTTP_REFERER')
        monitor.landing_page = request.META.get('HTTP_HOST') + request.META.get('PATH_INFO')
        monitor.frequency = 1
        monitor.save()
        
    if not request.user.is_authenticated:
        profile_context = {"status": "none"}
    else:
        profile=Profile.objects.filter(user=request.user)
       
        if profile.exists():
            profile=Profile.objects.get(user=request.user)
            profile_context=profile
    context = {"profile": profile_context, "course": course}        
    return render(request, 'website/course_detail.html', context)

def update_course(request, course_id):
    import json
    from django.http import JsonResponse
    from django.urls import reverse
    
    course = get_object_or_404(Course, pk=course_id)
    if(course.teacher.profile == request.user.profile):
        # Get user profile and student data
        profile = get_object_or_404(Profile, user=request.user)
        student = None
        try:
            student = Student.objects.get(profile=profile)
        except Student.DoesNotExist:
            pass  # User might be a teacher, not a student
        
        # Get all modules associated with this course
        modules = Module.objects.filter(course=course).order_by('number')
        
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
        
        if request.method == 'POST':
            # Update course data
            course.name = request.POST.get('name')
            course.description = request.POST.get('description')
            course.price = request.POST.get('price')
            course.small_description = request.POST.get('small_description')
            course.learned = request.POST.get('learned')
            tags = request.POST.get('tags', '').split(',')
            course.update_at = datetime.today()
            
            # Handle image upload
            if 'image_course' in request.FILES:
                course.image_course = request.FILES['image_course']

            # Clear existing tags and add new ones
            course.tags.clear()
            for tag in tags:
                tag = tag.strip()
                if tag:
                    obj, created = Tags.objects.get_or_create(name=tag)
                    course.tags.add(obj)
            course.save()
            
            # Check if module data is also submitted
            if 'module_id' in request.POST and request.POST.get('module_id'):
                module_id = request.POST.get('module_id')
                try:
                    module = Module.objects.get(id=module_id, course=course)
                    module_name = request.POST.get('module_name', '')
                    if module_name:
                        module.name = module_name
                        module.save()
                    
                    # Handle video uploads
                    video_files = request.FILES.getlist('video')
                    video_names = request.POST.getlist('video_names[]', [])
                    
                    for i, video in enumerate(video_files):
                        video_name = video_names[i] if i < len(video_names) else video.name.split('.')[0]
                        Video.objects.create(module=module, video=video, name=video_name, course=course)
                except Module.DoesNotExist:
                    pass  # Module not found, just continue
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == 'true':
                return JsonResponse({
                    'success': True, 
                    'message': 'Course and module updated successfully',
                    'redirect_url': reverse('course_detail', args=[course_id])
                })
            else:
                # Redirect to course detail page
                return redirect('course_detail', course_id=course.id)
        
        return render(request, 'website/update_course.html', {
            'course': course, 
            'modules': modules,
            'modules_json': json.dumps(modules_json),
            'profile': profile,
            'student': student
        })
    else:
        return redirect('course_detail', course_id=course.id)

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
        module=Module()
        module.name = module_name
        module.course=course
        module.number = module_number
        module.save()
        number=0
        for video in request.FILES.getlist('video'):
            video_name = video.name.split('.')[0]
            number += 1
            Video.objects.create(module=module, video=video, name=video_name, course=course, number=number)

        for note in request.POST.getlist('notes[]'):
            if note.strip():
                module.total_notes += 1
                Notes.objects.create(user=request.user, module=module, description=note, number=module.total_notes)

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

def make_teacher(request):
    r_profile=get_object_or_404(Profile, user=request.user)
    organization=Organization.objects.filter(profile=r_profile)
    if organization.exists():
        organization=Organization.objects.get(profile=r_profile)
        profiles = Profile.objects.all()
        context = {
            'profiles': profiles
        }
        
        if request.method == 'POST':
            profile_id=request.POST.get('profile_id')
            r_profile=get_object_or_404(Profile, id=profile_id)
            r_profile.status="Teacher"
            r_profile.save()
            teacher=Teacher.objects.create(profile=r_profile, organization=organization)
            student=get_object_or_404(Student,profile=r_profile)
            student.delete()
            teacher.save()
            return redirect('make_teacher')                           
        return render(request, 'website/make_teacher.html', context)
    else:
        return redirect('index')

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
        return redirect('login')
    enrollment, created = Enrollment.objects.get_or_create(course=course, student=request.user)
    if created:
        messages.success(request, f"You have successfully enrolled in {course.name}.")
    else:
        messages.warning(request, f"You are already enrolled in {course.name}.")
    return redirect(reverse('courseviewpage', args=[course_id]))

def analytics(request):
    return render(request, 'website/analytics.html')


# def create_quiz(request, video_id):
#     video = Video.objects.get(id=video_id)
#     if request.user.profile != video.module.course.teacher.profile:
#         return HttpResponse('You do not have permission to access this page')
#     if request.method == 'POST':
#         pass_mark = request.POST.get('pass_mark')
#         start_time_str = request.POST.get('timestamp')
#         if start_time_str:
#             start_time = timedelta(seconds=float(start_time_str))
#         else:
#             start_time = timedelta(seconds=0)

#         quiz = Quiz.objects.create(
#             video=video,
#             start_time=start_time,
#             pass_mark=pass_mark,
#         )

#         question_text = request.POST.get('question_text')
#         question = Question.objects.create(
#             quiz=quiz,
#             text=question_text,
#         )

#         answer1_text = request.POST.get('answer1_text')
#         answer1_is_correct = request.POST.get('answer1_is_correct') == 'on'
#         answer1 = Answer.objects.create(
#             question=question,
#             text=answer1_text,
#             is_correct=answer1_is_correct,
#         )

#         answer2_text = request.POST.get('answer2_text')
#         answer2_is_correct = request.POST.get('answer2_is_correct') == 'on'
#         answer2 = Answer.objects.create(
#             question=question,
#             text=answer2_text,
#             is_correct=answer2_is_correct,
#         )

#         answer3_text = request.POST.get('answer3_text')
#         answer3_is_correct = request.POST.get('answer3_is_correct') == 'on'
#         answer3 = Answer.objects.create(
#             question=question,
#             text=answer3_text,
#             is_correct=answer3_is_correct,
#         )

#         answer4_text = request.POST.get('answer4_text')
#         answer4_is_correct = request.POST.get('answer4_is_correct') == 'on'
#         answer4 = Answer.objects.create(
#             question=question,
#             text=answer4_text,
#             is_correct=answer4_is_correct,
#         )
#         return redirect('quiz_detail', quiz_id=quiz.id)

#     return render(request, 'website/create_quiz.html', {'video': video})



# def submit_quiz(request):
#     if request.method == 'POST':
#         quiz_id = request.POST.get('quiz_id')
#         question_ids = request.POST.getlist('question_ids[]')
#         answer_ids = request.POST.getlist('answer_ids[]')

#         # Do something with the form data, for example:
#         quiz = Quiz.objects.get(id=quiz_id)
#         total_marks = 0
#         obtained_marks = 0
#         for question_id, answer_id in zip(question_ids, answer_ids):
#             question = Question.objects.get(id=question_id)
#             answer = Answer.objects.get(id=answer_id)
#             if answer.is_correct:
#                 obtained_marks += question.marks
#             total_marks += question.marks
#         percentage = obtained_marks / total_marks * 100
#         if percentage >= quiz.pass_percentage:
#             message = 'Congratulations! You passed the quiz with a score of {}%.'.format(round(percentage))
#         else:
#             message = 'Sorry, you failed the quiz with a score of {}%.'.format(round(percentage))
#         return redirect('quiz_result', quiz_id=quiz_id, message=message)
#     else:
#         return redirect('home')