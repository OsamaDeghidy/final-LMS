from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from .models import Category, Course, Module, Video, Comment, SubComment, Notes, Monitor, Tags, Quiz, Question, Answer, Enrollment, Review
from user.models import Profile, Student, Organization, Teacher
from .utils import searchCourses

from django.contrib.gis.geoip2 import GeoIP2
from django_user_agents.utils import get_user_agent
import requests
import json

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
    enrollment = None
    progress = 0
    
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(course=course, student=request.user).first()
        if enrollment:
            is_enrolled = True
            # Update last accessed time and get progress
            from .utils import update_enrollment_progress
            progress = update_enrollment_progress(enrollment)
    
    if is_enrolled:
        context = {
            'course': course,
            'enrollment': enrollment,
            'progress': progress
        }
        return render(request, 'website/courseviewpage.html', context)
    else:
        return redirect('course_detail', course_id=course.id)

def courseviewpagevideo(request, course_id, video_id):
    course = get_object_or_404(Course, id=course_id)
    video = get_object_or_404(Video, id=video_id)
    is_enrolled = False
    enrollment = None
    video_progress = None
    
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
            
    if is_enrolled:
        quiz = Quiz.objects.filter(video=video).first()
        questions = quiz.question_set.all() if quiz else []
        
        context = {
            'course': course, 
            'video': video, 
            'questions': questions, 
            'quiz': quiz,
            'video_progress': video_progress
        }
        return render(request, 'website/courseviewvideo.html', context)
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
                course = Course(
                    name=name,
                    description=description,
                    image_course=image_course,
                    syllabus_pdf=syllabus_pdf,
                    materials_pdf=materials_pdf,
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
                                order=int(question_index)
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
                                            order=int(answer_index)
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
            # Update course data
            course.name = request.POST.get('name')
            course.description = request.POST.get('description')
            course.price = request.POST.get('price')
            course.small_description = request.POST.get('small_description')
            course.learned = request.POST.get('learned')
            course.level = request.POST.get('level')
            tags = request.POST.get('tags', '').split(',')
            course.update_at = datetime.today()
            
            # Update category if provided
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = Category.objects.get(pk=category_id)
                    course.category = category
                    logger.info(f"Updated category for course {course_id} to {category.name}")
                except Category.DoesNotExist:
                    logger.warning(f"Category with ID {category_id} not found")
            
            # Update organization if provided
            organization_id = request.POST.get('organization')
            if organization_id:
                try:
                    organization = Organization.objects.get(pk=organization_id)
                    course.organization = organization
                    logger.info(f"Updated organization for course {course_id} to {organization.name}")
                except Organization.DoesNotExist:
                    logger.warning(f"Organization with ID {organization_id} not found")
            
            # Handle image upload
            if 'image_course' in request.FILES:
                course.image_course = request.FILES['image_course']
                
            # Handle PDF uploads
            # Handle syllabus PDF
            if 'syllabus_pdf' in request.FILES:
                # If there's a new file, replace the old one
                if course.syllabus_pdf:
                    course.syllabus_pdf.delete(save=False)
                course.syllabus_pdf = request.FILES['syllabus_pdf']
                logger.info(f"Uploaded new syllabus PDF for course {course_id}: {request.FILES['syllabus_pdf'].name}")
            elif request.POST.get('delete_syllabus_pdf') == '1':
                # If delete flag is set and no new file is uploaded, delete the existing file
                if course.syllabus_pdf:
                    course.syllabus_pdf.delete(save=False)
                    course.syllabus_pdf = None
                    logger.info(f"Deleted syllabus PDF for course {course_id}")
                    
            # Handle materials PDF
            if 'materials_pdf' in request.FILES:
                # If there's a new file, replace the old one
                if course.materials_pdf:
                    course.materials_pdf.delete(save=False)
                course.materials_pdf = request.FILES['materials_pdf']
                logger.info(f"Uploaded new materials PDF for course {course_id}: {request.FILES['materials_pdf'].name}")
            elif request.POST.get('delete_materials_pdf') == '1':
                # If delete flag is set and no new file is uploaded, delete the existing file
                if course.materials_pdf:
                    course.materials_pdf.delete(save=False)
                    course.materials_pdf = None
                    logger.info(f"Deleted materials PDF for course {course_id}")

            # Clear existing tags and add new ones
            course.tags.clear()
            for tag in tags:
                tag = tag.strip()
                if tag:
                    obj, created = Tags.objects.get_or_create(name=tag)
                    course.tags.add(obj)
                    
            # Save course with all updates
            course.save()
            logger.info(f"Course {course_id} updated successfully with basic changes")
            
            # Process existing modules
            for key, value in request.POST.items():
                # Handle existing module updates
                if key.startswith('module_name_existing_'):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        module_id = parts[-1]  # Get the module ID from the end of the key
                        try:
                            # Ensure module_id is a valid integer
                            module_id = int(module_id)
                            module = Module.objects.get(id=module_id, course=course)
                            module.name = value
                            module.description = request.POST.get(f'module_description_existing_{module_id}', '')
                            module.save()
                            logger.info(f"Updated module {module_id} for course {course_id}")
                        except (ValueError, Module.DoesNotExist):
                            logger.warning(f"Could not update module with ID {module_id} for course {course_id}")
                            continue
                        
                # Handle module deletion
                elif key.startswith('delete_module_') and value == '1':
                    module_id = key.replace('delete_module_', '')
                    try:
                        # Ensure module_id is a valid integer
                        module_id = int(module_id)
                        module = Module.objects.get(id=module_id, course=course)
                        module.delete()
                        logger.info(f"Deleted module {module_id} from course {course_id}")
                    except (ValueError, Module.DoesNotExist):
                        logger.warning(f"Could not delete module with ID {module_id} for course {course_id}")
                        continue
            
            # Process new modules from dynamic form
            # First identify all new modules by looking for keys that match the pattern
            new_module_ids = set()
            for key in request.POST.keys():
                # Look for module_name_new_TIMESTAMP pattern
                if key.startswith('module_name_new_'):
                    module_id = key.replace('module_name_new_', '')
                    new_module_ids.add(module_id)
                # Also check for the pattern from the JavaScript-generated modules
                elif key.startswith('module_title_new_'):
                    module_id = key.replace('module_title_new_', '')
                    new_module_ids.add(module_id)
            
            logger.info(f"Found {len(new_module_ids)} new modules to process")
            
            # Process each new module
            for module_id in new_module_ids:
                # Get module name from either naming convention
                module_name = request.POST.get(f'module_name_new_{module_id}') or \
                              request.POST.get(f'module_title_new_{module_id}')
                
                if not module_name or not module_name.strip():
                    logger.warning(f"Skipping new module {module_id} with empty name")
                    continue
                
                # Get module description
                module_description = request.POST.get(f'module_description_new_{module_id}', '')
                
                # Create the new module
                new_module = Module.objects.create(
                    course=course,
                    name=module_name,
                    description=module_description,
                    number=course.total_module + 1  # Set number to be after existing modules
                )
                course.total_module += 1
                logger.info(f"Created new module {new_module.id} for course {course_id}")
                
                # Process videos for this module if any
                video_files = request.FILES.getlist(f'module_videos_new_{module_id}')
                video_names = []
                
                # Get video names
                for key in request.POST.keys():
                    if key.startswith(f'video_name_new_{module_id}_'):
                        video_name = request.POST.get(key)
                        if video_name and video_name.strip():
                            video_names.append(video_name)
                
                # Create videos
                for i, video in enumerate(video_files):
                    video_name = video_names[i] if i < len(video_names) else video.name.split('.')[0]
                    Video.objects.create(
                        name=video_name,
                        module=new_module,
                        course=course,
                        video=video,
                        number=i+1
                    )
                    new_module.total_video += 1
                
                # Process notes for this module
                for key in request.POST.keys():
                    if key.startswith(f'note_new_{module_id}_'):
                        note_text = request.POST.get(key)
                        if note_text and note_text.strip():
                            Notes.objects.create(
                                user=request.user,
                                module=new_module,
                                description=note_text
                            )
                            new_module.total_notes += 1
                
                # Process quiz if exists
                has_quiz = request.POST.get(f'has_quiz_new_{module_id}')
                if has_quiz == '1' or has_quiz == 'on':
                    quiz_title = request.POST.get(f'quiz_title_new_{module_id}', f'Quiz for {module_name}')
                    quiz_description = request.POST.get(f'quiz_description_new_{module_id}', '')
                    quiz_pass_mark = request.POST.get(f'quiz_pass_mark_new_{module_id}', 50)
                    quiz_time_limit = request.POST.get(f'quiz_time_limit_new_{module_id}', 10)
                    
                    # Create quiz
                    quiz = Quiz.objects.create(
                        title=quiz_title,
                        description=quiz_description,
                        module=new_module,
                        course=course,
                        quiz_type='module',
                        pass_mark=float(quiz_pass_mark),
                        time_limit=int(quiz_time_limit),
                        is_active=True
                    )
                    
                    # Process questions
                    question_indices = set()
                    for key in request.POST.keys():
                        if key.startswith(f'question_text_new_{module_id}_'):
                            question_index = key.split(f'question_text_new_{module_id}_')[1]
                            question_indices.add(question_index)
                    
                    for question_index in question_indices:
                        question_text = request.POST.get(f'question_text_new_{module_id}_{question_index}')
                        if not question_text or not question_text.strip():
                            continue
                        
                        question_type = request.POST.get(f'question_type_new_{module_id}_{question_index}', 'multiple_choice')
                        
                        # Create question
                        question = Question.objects.create(
                            quiz=quiz,
                            text=question_text,
                            question_type=question_type,
                            points=1,
                            order=int(question_index) if question_index.isdigit() else 0
                        )
                        
                        # Process answers based on question type
                        if question_type == 'multiple_choice':
                            correct_answer = request.POST.get(f'correct_answer_new_{module_id}_{question_index}')
                            
                            # Get all answers for this question
                            answer_indices = set()
                            for answer_key in request.POST.keys():
                                if answer_key.startswith(f'answer_text_new_{module_id}_{question_index}_'):
                                    answer_index = answer_key.split('_')[-1]
                                    answer_indices.add(answer_index)
                            
                            for answer_index in answer_indices:
                                answer_text = request.POST.get(f'answer_text_new_{module_id}_{question_index}_{answer_index}')
                                if answer_text and answer_text.strip():
                                    is_correct = (correct_answer == answer_index)
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_text,
                                        is_correct=is_correct,
                                        order=int(answer_index) if answer_index.isdigit() else 0
                                    )
                        elif question_type == 'true_false':
                            correct_answer = request.POST.get(f'correct_answer_new_{module_id}_{question_index}')
                            
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
                            answer_text = request.POST.get(f'answer_short_new_{module_id}_{question_index}', '')
                            Answer.objects.create(
                                question=question,
                                text=answer_text,
                                is_correct=True,
                                order=0
                            )
                
                # Save the module with all updates
                new_module.save()
            
            # Process quizzes
            # Process existing questions first
            for key, value in request.POST.items():
                # Handle existing questions
                if key.startswith('question_text_existing_'):
                    parts = key.split('_')
                    if len(parts) >= 5:  # Format: question_text_existing_MODULE_ID_QUESTION_ID
                        module_id_str = parts[3]
                        question_id_str = parts[4]
                        
                        # If we have a question ID, use it directly
                        if question_id_str and question_id_str.isdigit():
                            question_id = int(question_id_str)
                            try:
                                # Get the existing question
                                question = Question.objects.get(id=question_id)
                                quiz = question.quiz
                                module = quiz.module
                                
                                # Make sure this question belongs to this course
                                if module.course.id != course.id:
                                    logger.warning(f"Question {question_id} does not belong to course {course_id}")
                                    continue
                                
                                # Update question
                                question_type = request.POST.get(f'question_type_existing_{module_id_str}_{question_id}', question.question_type)
                                question.text = value
                                question.question_type = question_type
                                question.save()
                                logger.info(f"Updated existing question {question_id} for module {module.id}")
                                
                                # Process answers based on question type
                                if question_type == 'multiple_choice':
                                    # Get all answer texts for this question
                                    answer_keys = [k for k in request.POST.keys() if k.startswith(f'answer_text_existing_{question_id}_')]
                                    
                                    # Delete existing answers for this question
                                    Answer.objects.filter(question=question).delete()
                                    
                                    # Get the correct answer value
                                    correct_answer_value = request.POST.get(f'correct_answer_existing_{question_id}', '')
                                    logger.info(f"Correct answer value for question {question_id}: {correct_answer_value}")
                                    
                                    # Create new answers
                                    for answer_key in answer_keys:
                                        answer_index = answer_key.split('_')[-1]
                                        answer_text = request.POST.get(answer_key)
                                        is_correct = (correct_answer_value == answer_index)
                                        
                                        Answer.objects.create(
                                            question=question,
                                            text=answer_text,
                                            is_correct=is_correct
                                        )
                                        logger.info(f"Created answer for question {question_id}: {answer_text}, correct: {is_correct}")
                                        
                                elif question_type == 'true_false':
                                    # Delete existing answers
                                    Answer.objects.filter(question=question).delete()
                                    
                                    # Get the correct answer value
                                    correct_answer_value = request.POST.get(f'correct_answer_existing_{question_id}', '')
                                    
                                    # Create True answer
                                    Answer.objects.create(
                                        question=question,
                                        text="صح",
                                        is_correct=correct_answer_value == '0'
                                    )
                                    
                                    # Create False answer
                                    Answer.objects.create(
                                        question=question,
                                        text="خطأ",
                                        is_correct=correct_answer_value == '1'
                                    )
                                elif question_type == 'short_answer':
                                    # Delete existing answers
                                    Answer.objects.filter(question=question).delete()
                                    
                                    # Create the correct answer
                                    correct_answer = request.POST.get(f'answer_short_existing_{question_id}', '')
                                    Answer.objects.create(
                                        question=question,
                                        text=correct_answer,
                                        is_correct=True
                                    )
                            except Question.DoesNotExist:
                                logger.warning(f"Question with ID {question_id} not found")
                                continue
            
            # Then process new questions for existing modules
            for key, value in request.POST.items():
                if key.startswith('question_text_') and not key.startswith('question_text_existing_'):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        module_id = parts[2]
                        question_index = parts[3] if len(parts) > 3 else '0'
                        
                        try:
                            # Ensure module_id is a valid integer
                            if not module_id.isdigit():
                                continue
                            module_id = int(module_id)
                            module = Module.objects.get(id=module_id, course=course)
                            
                            # Get or create quiz for this module
                            quiz, created = Quiz.objects.get_or_create(
                                module=module,
                                defaults={'name': f"Quiz for {module.name}"}
                            )
                            
                            # Create or update question
                            question_type = request.POST.get(f'question_type_{module_id}_{question_index}', 'multiple_choice')
                            question_text = value
                            
                            # Check if this is an existing question or a new one
                            question_id = request.POST.get(f'question_id_{module_id}_{question_index}', '')
                            
                            if question_id and question_id.isdigit():
                                # Update existing question
                                try:
                                    question = Question.objects.get(id=int(question_id), quiz=quiz)
                                    question.text = question_text
                                    question.question_type = question_type
                                    question.save()
                                    logger.info(f"Updated question {question_id} for module {module_id}")
                                except Question.DoesNotExist:
                                    continue
                            else:
                                # Create new question
                                question = Question.objects.create(
                                    quiz=quiz,
                                    text=question_text,
                                    question_type=question_type
                                )
                                logger.info(f"Created new question {question.id} for module {module_id}")
                            
                            # Process answers for this question
                            if question_type == 'multiple_choice':
                                # Get all answer texts and correct flags for this question
                                answer_keys = [k for k in request.POST.keys() if k.startswith(f'answer_text_{module_id}_{question_index}_')]
                                
                                # Delete existing answers for this question
                                Answer.objects.filter(question=question).delete()
                                
                                # Get the correct answer value
                                correct_answer_value = request.POST.get(f'correct_answer_{module_id}_{question_index}', '')
                                
                                # Create new answers
                                for answer_key in answer_keys:
                                    answer_index = answer_key.split('_')[-1]
                                    answer_text = request.POST.get(answer_key)
                                    is_correct = correct_answer_value == answer_index
                                    
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_text,
                                        is_correct=is_correct
                                    )
                            elif question_type == 'true_false':
                                # Delete existing answers
                                Answer.objects.filter(question=question).delete()
                                
                                # Create True answer
                                Answer.objects.create(
                                    question=question,
                                    text="صح",
                                    is_correct=request.POST.get(f'correct_answer_{module_id}_{question_index}') == '0'
                                )
                                
                                # Create False answer
                                Answer.objects.create(
                                    question=question,
                                    text="خطأ",
                                    is_correct=request.POST.get(f'correct_answer_{module_id}_{question_index}') == '1'
                                )
                            elif question_type == 'short_answer':
                                # Delete existing answers
                                Answer.objects.filter(question=question).delete()
                                
                                # Create the correct answer
                                correct_answer = request.POST.get(f'answer_short_{module_id}_{question_index}', '')
                                Answer.objects.create(
                                    question=question,
                                    text=correct_answer,
                                    is_correct=True
                                )
                        except Module.DoesNotExist:
                            continue
            
            # Add success message
            messages.success(request, 'تم تحديث الدورة بنجاح')
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == 'true':
                return JsonResponse({
                    'success': True, 
                    'message': 'تم تحديث الدورة بنجاح',
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
            'student': student,
            'categories': categories,
            'organizations': organizations,
            'tags_string': tags_string
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

@csrf_exempt
def mark_video_watched(request, video_id):
    """API endpoint to mark a video as watched"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)
    
    try:
        video = Video.objects.get(id=video_id)
        
        # Get or create video progress
        video_progress, created = VideoProgress.objects.get_or_create(
            student=request.user,
            video=video,
            defaults={'watched': False}
        )
        
        # Mark as watched
        video_progress.mark_as_watched()
        
        # Update enrollment progress
        enrollment = Enrollment.objects.filter(
            student=request.user, 
            course=video.course
        ).first()
        
        if enrollment:
            from .utils import update_enrollment_progress
            progress = update_enrollment_progress(enrollment)
            return JsonResponse({
                'status': 'success', 
                'message': 'Video marked as watched',
                'progress': progress
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'User not enrolled in this course'}, status=400)
            
    except Video.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Video not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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
    elif pdf_type == 'materials_pdf' and course.materials_pdf:
        # Delete the file
        course.materials_pdf.delete(save=False)
        course.materials_pdf = None
        course.save()
    else:
        messages.error(request, 'لم يتم العثور على الملف المطلوب')
    
    # Redirect back to the update course page
    return redirect('update_course', course_id=course_id)


def course_category(request, category_slug):
    """
    View to display all courses belonging to a specific category
    """
    # Get the category or return 404 if not found
    category = get_object_or_404(Category, name=category_slug)
    
    # Get all courses in this category
    courses = Course.objects.filter(category=category, status='published')
    
    context = {
        'category': category,
        'courses': courses,
    }
    
    return render(request, 'website/category_courses.html', context)


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