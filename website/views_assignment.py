from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Assignment, AssignmentSubmission, Course, Module, Attachment
from user.models import Teacher, Profile
from .utils_permissions import is_teacher, is_course_teacher, get_teacher

def assignment_list(request, course_id):
    """View all assignments for a course"""
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('-created_at')
    
    # Check if user is teacher of the course or a student enrolled in the course
    is_teacher = request.user.is_authenticated and hasattr(request.user, 'teacher') and course.teacher == request.user.teacher
    is_enrolled = request.user.is_authenticated and course.enrollments.filter(student=request.user).exists()
    
    if not (is_teacher or is_enrolled):
        messages.error(request, 'ليس لديك صلاحية لعرض الواجبات لهذه الدورة')
        return redirect('course_detail', course_id=course_id)
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'course': course,
        'assignments': assignments,
        'is_teacher': is_teacher,
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/assignment_list.html', context)

@login_required
def create_assignment(request, course_id):
    """Create a new assignment for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is teacher of the course
    is_teacher = False
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            is_teacher = (course.teacher == teacher)
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        pass
        
    if not is_teacher:
        messages.error(request, 'ليس لديك صلاحية لإضافة واجبات لهذه الدورة')
        return redirect('course_detail', course_id=course_id)
    
    modules = Module.objects.filter(course=course)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        module_id = request.POST.get('module')
        due_date_str = request.POST.get('due_date')
        points = request.POST.get('points', 100)
        allow_late = request.POST.get('allow_late_submissions') == 'on'
        late_penalty = request.POST.get('late_submission_penalty', 0)
        
        if not title or not description:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
            return render(request, 'website/assignment/create_assignment.html', {'course': course, 'modules': modules})
        
        # Create the assignment
        assignment = Assignment.objects.create(
            title=title,
            course=course,
            module_id=module_id if module_id else None,
            description=description,
            due_date=due_date_str if due_date_str else None,
            points=points,
            allow_late_submissions=allow_late,
            late_submission_penalty=late_penalty
        )
        
        # Handle file attachments
        files = request.FILES.getlist('attachments')
        if files:
            content_type = ContentType.objects.get_for_model(Assignment)
            for file in files:
                attachment = Attachment.objects.create(
                    file=file,
                    content_type=content_type,
                    object_id=assignment.id
                )
        
        messages.success(request, 'تم إنشاء الواجب بنجاح')
        # إعادة التوجيه إلى صفحة الواجبات الرئيسية بدلاً من صفحة تفاصيل الواجب
        return redirect('all_assignments')
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'course': course,
        'modules': modules,
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/create_assignment.html', context)

@login_required
def update_assignment(request, assignment_id):
    """Update an existing assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Check if user is teacher of the course
    is_teacher = False
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            is_teacher = (course.teacher == teacher)
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        pass
        
    if not is_teacher:
        messages.error(request, 'ليس لديك صلاحية لتعديل هذا الواجب')
        return redirect('assignment_detail', assignment_id=assignment_id)
    
    modules = Module.objects.filter(course=course)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        module_id = request.POST.get('module')
        due_date_str = request.POST.get('due_date')
        points = request.POST.get('points', 100)
        allow_late = request.POST.get('allow_late_submissions') == 'on'
        late_penalty = request.POST.get('late_submission_penalty', 0)
        
        if not title or not description:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
            return render(request, 'website/assignment/update_assignment.html', 
                          {'assignment': assignment, 'course': course, 'modules': modules})
        
        # Update the assignment
        assignment.title = title
        assignment.description = description
        assignment.module_id = module_id if module_id else None
        assignment.due_date = due_date_str if due_date_str else None
        assignment.points = points
        assignment.allow_late_submissions = allow_late
        assignment.late_submission_penalty = late_penalty
        assignment.save()
        
        # Handle file attachments
        files = request.FILES.getlist('attachments')
        if files:
            content_type = ContentType.objects.get_for_model(Assignment)
            for file in files:
                attachment = Attachment.objects.create(
                    file=file,
                    content_type=content_type,
                    object_id=assignment.id
                )
        
        messages.success(request, 'تم تحديث الواجب بنجاح')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'assignment': assignment,
        'course': course,
        'modules': modules,
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/update_assignment.html', context)

@login_required
def delete_assignment(request, assignment_id):
    """Delete an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Check if user is teacher of the course
    is_teacher = False
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            is_teacher = (course.teacher == teacher)
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        pass
        
    if not is_teacher:
        messages.error(request, 'ليس لديك صلاحية لحذف هذا الواجب')
        return redirect('assignment_detail', assignment_id=assignment_id)
    
    if request.method == 'POST':
        course_id = course.id
        assignment.delete()
        messages.success(request, 'تم حذف الواجب بنجاح')
        return redirect('assignment_list', course_id=course_id)
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'assignment': assignment,
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/delete_assignment.html', context)

def assignment_detail(request, assignment_id):
    """View details of an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Check if user is teacher of the course or a student enrolled in the course
    is_teacher = request.user.is_authenticated and hasattr(request.user, 'teacher') and course.teacher == request.user.teacher
    is_enrolled = request.user.is_authenticated and course.enrollments.filter(student=request.user).exists()
    
    if not (is_teacher or is_enrolled):
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الواجب')
        return redirect('course_detail', course_id=course.id)
    
    # Get attachments for the assignment
    content_type = ContentType.objects.get_for_model(Assignment)
    attachments = Attachment.objects.filter(
        content_type=content_type,
        object_id=assignment.id
    )
    
    # Get user's submission if exists
    user_submission = None
    if request.user.is_authenticated and not is_teacher:
        user_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            user=request.user
        ).first()
    
    # Get all submissions if teacher
    submissions = None
    if is_teacher:
        submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('-submitted_at')
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'assignment': assignment,
        'course': course,
        'attachments': attachments,
        'user_submission': user_submission,
        'submissions': submissions,
        'is_teacher': is_teacher,
        'is_enrolled': is_enrolled,
        'now': timezone.now(),
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/assignment_detail.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """Submit an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Check if user is enrolled in the course
    if not course.enrollments.filter(student=request.user).exists():
        messages.error(request, 'ليس لديك صلاحية لتسليم هذا الواجب')
        return redirect('course_detail', course_id=course.id)
    
    # Check if assignment is past due date and late submissions not allowed
    is_late = assignment.due_date and timezone.now() > assignment.due_date
    if is_late and not assignment.allow_late_submissions:
        messages.error(request, 'انتهى وقت تسليم هذا الواجب')
        return redirect('assignment_detail', assignment_id=assignment_id)
    
    # Check if user already has a submission
    existing_submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        user=request.user
    ).first()
    
    if request.method == 'POST':
        submission_text = request.POST.get('submission_text')
        
        if existing_submission:
            # Update existing submission
            existing_submission.submission_text = submission_text
            existing_submission.submitted_at = timezone.now()
            existing_submission.status = 'submitted'
            existing_submission.save()
            submission = existing_submission
        else:
            # Create new submission
            submission = AssignmentSubmission.objects.create(
                assignment=assignment,
                user=request.user,
                submission_text=submission_text,
                is_late=is_late
            )
        
        # Handle file attachments
        files = request.FILES.getlist('attachments')
        if files:
            content_type = ContentType.objects.get_for_model(AssignmentSubmission)
            for file in files:
                attachment = Attachment.objects.create(
                    file=file,
                    content_type=content_type,
                    object_id=submission.id
                )
        
        messages.success(request, 'تم تسليم الواجب بنجاح')
        return redirect('assignment_detail', assignment_id=assignment_id)
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'assignment': assignment,
        'course': course,
        'existing_submission': existing_submission,
        'now': timezone.now(),
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/submit_assignment.html', context)

@login_required
def grade_submission(request, submission_id):
    """Grade a student's assignment submission"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    course = assignment.course
    
    # Check if user is teacher of the course
    is_teacher = False
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.status == 'Teacher':
            teacher = Teacher.objects.get(profile=profile)
            is_teacher = (course.teacher == teacher)
    except (Profile.DoesNotExist, Teacher.DoesNotExist):
        pass
        
    if not is_teacher:
        messages.error(request, 'ليس لديك صلاحية لتقييم هذا الواجب')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        status = request.POST.get('status', 'graded')
        
        try:
            grade = float(grade)
            if grade < 0 or grade > assignment.points:
                raise ValueError
        except ValueError:
            messages.error(request, f'يرجى إدخال درجة صحيحة بين 0 و {assignment.points}')
            return redirect('grade_submission', submission_id=submission_id)
        
        # Update submission with grade and feedback
        submission.grade = grade
        submission.feedback = feedback
        submission.status = status
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, 'تم تقييم الواجب بنجاح')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    # Get attachments for the submission
    content_type = ContentType.objects.get_for_model(AssignmentSubmission)
    attachments = Attachment.objects.filter(
        content_type=content_type,
        object_id=submission.id
    )
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'course': course,
        'attachments': attachments,
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/grade_submission.html', context)

def all_assignments(request):
    """View all assignments for enrolled courses or courses taught by the user"""
    if not request.user.is_authenticated:
        messages.error(request, 'يرجى تسجيل الدخول لعرض الواجبات')
        return redirect('login')
    
    # Get assignments for courses the user is teaching
    teaching_assignments = []
    teacher_courses = []
    
    # Check if user is a teacher
    teacher = get_teacher(request.user)
    if teacher:
        teacher_courses = Course.objects.filter(teacher=teacher)
        teaching_assignments = Assignment.objects.filter(course__in=teacher_courses).order_by('-created_at')
    
    # Get assignments for courses the user is enrolled in
    enrolled_courses = Course.objects.filter(enrollments__student=request.user)
    enrolled_assignments = Assignment.objects.filter(course__in=enrolled_courses).order_by('-created_at')
    
    # Get user's submissions for enrolled assignments
    submissions_by_assignment = {}
    for assignment in enrolled_assignments:
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            user=request.user
        ).first()
        if submission:
            submissions_by_assignment[assignment.id] = submission
    
    # Get user profile for dashboard template
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    context = {
        'teaching_assignments': teaching_assignments,
        'enrolled_assignments': enrolled_assignments,
        'submissions_by_assignment': submissions_by_assignment,
        'is_teacher': is_teacher(request.user),
        'teacher_courses': teacher_courses,
        'now': timezone.now(),
        'profile': profile,  # Add profile to context
        'student': getattr(request.user, 'student', None)  # Add student to context if exists
    }
    return render(request, 'website/assignment/all_assignments.html', context)

@login_required
@csrf_exempt
def delete_attachment(request, attachment_id):
    """Delete an attachment"""
    if request.method == 'POST':
        attachment = get_object_or_404(Attachment, id=attachment_id)
        
        # Check if the user has permission to delete this attachment
        # For assignment attachments, only the teacher can delete
        # For submission attachments, only the submitting user can delete
        content_type = attachment.content_type
        if content_type.model == 'assignment':
            assignment = get_object_or_404(Assignment, id=attachment.object_id)
            try:
                profile = Profile.objects.get(user=request.user)
                teacher = Teacher.objects.get(profile=profile)
                if assignment.course.teacher != teacher:
                    return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لحذف هذا المرفق'}, status=403)
            except (Profile.DoesNotExist, Teacher.DoesNotExist):
                return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لحذف هذا المرفق'}, status=403)
        elif content_type.model == 'assignmentsubmission':
            submission = get_object_or_404(AssignmentSubmission, id=attachment.object_id)
            if submission.user != request.user:
                return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لحذف هذا المرفق'}, status=403)
        
        # Delete the file from storage
        attachment.file.delete(save=False)
        # Delete the attachment record
        attachment.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مسموح بها'}, status=405)
