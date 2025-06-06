from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, Sum
from django.contrib import messages
from .models import Course, User, Attendance, Module, Video
import json
from datetime import datetime
from django.contrib.auth.models import User


@login_required
def attendance_dashboard(request):
    """
    Dashboard view for attendance tracking.
    For students: Shows their attendance records
    For teachers: Shows attendance records for their courses
    """
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    
    if is_teacher:
        # Get courses taught by this teacher
        courses = Course.objects.filter(teacher__profile__user=user)
        
        # Get attendance statistics for each course
        course_stats = []
        for course in courses:
            total_students = course.enroller_user.count()
            attendance_records = Attendance.objects.filter(course=course)
            
            # Calculate attendance rate
            total_sessions = attendance_records.values('date', 'video').distinct().count()
            if total_sessions > 0 and total_students > 0:
                expected_records = total_sessions * total_students
                actual_records = attendance_records.filter(is_present=True).count()
                attendance_rate = (actual_records / expected_records) * 100
            else:
                attendance_rate = 0
                
            course_stats.append({
                'course': course,
                'total_students': total_students,
                'total_sessions': total_sessions,
                'attendance_rate': attendance_rate,
            })
            
        context = {
            'is_teacher': True,
            'course_stats': course_stats,
        }
    else:
        # Get courses enrolled by this student
        enrolled_courses = Course.objects.filter(enroller_user=user)
        
        # Get attendance records for each course
        course_attendance = []
        for course in enrolled_courses:
            attendance_records = Attendance.objects.filter(user=user, course=course)
            total_sessions = attendance_records.count()
            attended_sessions = attendance_records.filter(is_present=True).count()
            
            if total_sessions > 0:
                attendance_rate = (attended_sessions / total_sessions) * 100
            else:
                attendance_rate = 0
                
            course_attendance.append({
                'course': course,
                'total_sessions': total_sessions,
                'attended_sessions': attended_sessions,
                'attendance_rate': attendance_rate,
            })
            
        context = {
            'is_teacher': False,
            'course_attendance': course_attendance,
        }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/dashboard.html', context)


@login_required
def course_attendance(request, course_id):
    """
    View attendance records for a specific course
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    
    # Check if user is authorized to view this course's attendance
    if is_teacher and course.teacher.profile.user != user:
        messages.error(request, 'ليس لديك صلاحية لعرض سجل الحضور لهذه الدورة')
        return redirect('attendance_dashboard')
    
    if not is_teacher and user not in course.enroller_user.all():
        messages.error(request, 'يجب أن تكون مسجلاً في الدورة لعرض سجل الحضور')
        return redirect('attendance_dashboard')
    
    # Get all modules and videos for this course
    modules = Module.objects.filter(course=course).prefetch_related('video_set')
    
    if is_teacher:
        # Get all students enrolled in this course
        students = course.enroller_user.all()
        
        # Get attendance records for all students
        attendance_records = Attendance.objects.filter(course=course)
        
        # Calculate attendance statistics
        student_stats = []
        for student in students:
            student_records = attendance_records.filter(user=student)
            total_sessions = student_records.count()
            attended_sessions = student_records.filter(is_present=True).count()
            
            if total_sessions > 0:
                attendance_rate = (attended_sessions / total_sessions) * 100
            else:
                attendance_rate = 0
                
            student_stats.append({
                'student': student,
                'total_sessions': total_sessions,
                'attended_sessions': attended_sessions,
                'attendance_rate': attendance_rate,
            })
            
        context = {
            'course': course,
            'modules': modules,
            'is_teacher': True,
            'student_stats': student_stats,
        }
    else:
        # Get attendance records for this student
        attendance_records = Attendance.objects.filter(user=user, course=course)
        
        context = {
            'course': course,
            'modules': modules,
            'is_teacher': False,
            'attendance_records': attendance_records,
        }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/course_attendance.html', context)


@login_required
@require_POST
def mark_attendance(request):
    """
    API endpoint to mark attendance for a video or live session
    """
    user = request.user
    course_id = request.POST.get('course_id')
    video_id = request.POST.get('video_id')
    module_id = request.POST.get('module_id')
    is_present = request.POST.get('is_present', 'true') == 'true'
    
    # Validate input
    if not course_id:
        return JsonResponse({'status': 'error', 'message': 'معرف الدورة مطلوب'}, status=400)
    
    # Get course
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'الدورة غير موجودة'}, status=404)
    
    # Check if user is enrolled in the course
    if user not in course.enroller_user.all():
        return JsonResponse({'status': 'error', 'message': 'يجب أن تكون مسجلاً في الدورة لتسجيل الحضور'}, status=403)
    
    # Get video if provided
    video = None
    if video_id:
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'الفيديو غير موجود'}, status=404)
    
    # Get module if provided
    module = None
    if module_id:
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'الوحدة غير موجودة'}, status=404)
    
    # Check if attendance already recorded for today
    today = timezone.now().date()
    existing_attendance = Attendance.objects.filter(
        user=user,
        course=course,
        date=today,
        video=video
    ).first()
    
    if existing_attendance:
        # Update existing attendance record
        existing_attendance.is_present = is_present
        if is_present and not existing_attendance.time_in:
            existing_attendance.time_in = timezone.now()
        existing_attendance.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تحديث سجل الحضور بنجاح',
            'attendance_id': existing_attendance.id
        })
    else:
        # Create new attendance record
        attendance = Attendance.objects.create(
            user=user,
            course=course,
            module=module,
            video=video,
            date=today,
            time_in=timezone.now() if is_present else None,
            is_present=is_present
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل الحضور بنجاح',
            'attendance_id': attendance.id
        })


@login_required
@require_POST
def mark_attendance_out(request):
    """
    API endpoint to mark attendance out time
    """
    # Parse JSON data if content type is application/json
    if request.content_type == 'application/json':
        import json
        data = json.loads(request.body)
        attendance_id = data.get('attendance_id')
    else:
        attendance_id = request.POST.get('attendance_id')
        
    if not attendance_id:
        return JsonResponse({'status': 'error', 'message': 'Attendance ID is required'}, status=400)
    
    try:
        attendance = Attendance.objects.get(id=attendance_id, user=request.user)
    except Attendance.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attendance record not found'}, status=404)
    
    # Mark attendance out time
    attendance.time_out = timezone.now()
    attendance.save()  # This will calculate duration automatically
    
    return JsonResponse({
        'status': 'success',
        'message': 'تم تسجيل وقت المغادرة بنجاح',
        'duration': str(attendance.duration)
    })


@login_required
def attendance_report(request, course_id):
    """
    Generate attendance report for a course
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    
    # Check if user is authorized to view this report
    if is_teacher and course.teacher.profile.user != user:
        messages.error(request, 'ليس لديك صلاحية لعرض تقرير الحضور لهذه الدورة')
        return redirect('attendance_dashboard')
    
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Parse dates
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to 30 days ago
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to today
            end_date = timezone.now().date()
    except ValueError:
        messages.error(request, 'تنسيق التاريخ غير صحيح')
        start_date = timezone.now().date() - timedelta(days=30)
        end_date = timezone.now().date()
    
    # Filter attendance records by date range
    attendance_records = Attendance.objects.filter(
        course=course,
        date__gte=start_date,
        date__lte=end_date
    )
    
    if is_teacher:
        # Group by student
        students = course.enroller_user.all()
        student_attendance = []
        
        for student in students:
            student_records = attendance_records.filter(user=student)
            total_sessions = student_records.count()
            attended_sessions = student_records.filter(is_present=True).count()
            
            if total_sessions > 0:
                attendance_rate = (attended_sessions / total_sessions) * 100
            else:
                attendance_rate = 0
                
            # Calculate average duration
            durations = [record.duration for record in student_records if record.duration]
            if durations:
                total_seconds = sum((duration.total_seconds() for duration in durations))
                avg_duration = timedelta(seconds=total_seconds / len(durations))
            else:
                avg_duration = timedelta(0)
                
            student_attendance.append({
                'student': student,
                'total_sessions': total_sessions,
                'attended_sessions': attended_sessions,
                'attendance_rate': attendance_rate,
                'avg_duration': avg_duration,
            })
            
        context = {
            'course': course,
            'is_teacher': True,
            'student_attendance': student_attendance,
            'start_date': start_date,
            'end_date': end_date,
        }
    else:
        # Filter by current user
        user_records = attendance_records.filter(user=user)
        
        # Group by video/module
        video_attendance = []
        for record in user_records:
            video_name = record.video.name if record.video else "جلسة مباشرة"
            module_name = record.module.name if record.module else ""
            
            video_attendance.append({
                'date': record.date,
                'video_name': video_name,
                'module_name': module_name,
                'is_present': record.is_present,
                'duration': record.duration,
            })
            
        context = {
            'course': course,
            'is_teacher': False,
            'video_attendance': video_attendance,
            'start_date': start_date,
            'end_date': end_date,
        }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/report.html', context)


@login_required
def student_details(request, course_id, student_id):
    """
    AJAX view to load student attendance details for a specific course
    """
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(User, id=student_id)
    user = request.user
    
    # Security check - only teachers of this course can view student details
    if not (hasattr(user, 'profile') and user.profile.status == 'Teacher' and course.teacher.profile.user == user):
        return JsonResponse({'status': 'error', 'message': 'غير مصرح لك بعرض هذه البيانات'}, status=403)
    
    # Get attendance records for this student in this course
    records = Attendance.objects.filter(user=student, course=course).order_by('-date')
    
    # Calculate statistics
    total_sessions = records.count()
    attended_sessions = records.filter(is_present=True).count()
    
    if total_sessions > 0:
        attendance_rate = (attended_sessions / total_sessions) * 100
    else:
        attendance_rate = 0
    
    # Calculate average duration
    durations = [record.duration for record in records if record.duration]
    if durations:
        total_seconds = sum((duration.total_seconds() for duration in durations))
        avg_duration = timedelta(seconds=total_seconds / len(durations))
    else:
        avg_duration = timedelta(0)
    
    context = {
        'student': student,
        'course': course,
        'student_records': records,
        'total_sessions': total_sessions,
        'attended_sessions': attended_sessions,
        'attendance_rate': attendance_rate,
        'avg_duration': avg_duration
    }
    
    # Add profile data to context
    if hasattr(user, 'profile'):
        context['profile'] = user.profile
    
    return render(request, 'website/attendance/student_details.html', context)


@login_required
def print_attendance_report(request, course_id):
    """
    Generate a printable attendance report for a course
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    is_teacher = hasattr(user, 'profile') and user.profile.status == 'Teacher'
    
    # Check if user is authorized to view this course's attendance
    if is_teacher and course.teacher.profile.user != user:
        messages.error(request, 'ليس لديك صلاحية لعرض سجل الحضور لهذه الدورة')
        return redirect('attendance_dashboard')
    
    if not is_teacher and user not in course.enroller_user.all():
        messages.error(request, 'يجب أن تكون مسجلاً في الدورة لعرض سجل الحضور')
        return redirect('attendance_dashboard')
    
    # Get date range from request or default to last 30 days
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date() - timedelta(days=30)
        
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
    
    # Get attendance records for this course within date range
    attendance_records = Attendance.objects.filter(
        course=course,
        date__gte=start_date,
        date__lte=end_date
    )
    
    if is_teacher:
        # Group by student
        students = course.enroller_user.all()
        student_attendance = []
        
        for student in students:
            student_records = attendance_records.filter(user=student)
            total_sessions = student_records.count()
            attended_sessions = student_records.filter(is_present=True).count()
            
            if total_sessions > 0:
                attendance_rate = (attended_sessions / total_sessions) * 100
            else:
                attendance_rate = 0
                
            # Calculate average duration
            durations = [record.duration for record in student_records if record.duration]
            if durations:
                total_seconds = sum((duration.total_seconds() for duration in durations))
                avg_duration = timedelta(seconds=total_seconds / len(durations))
            else:
                avg_duration = timedelta(0)
                
            student_attendance.append({
                'student': student,
                'total_sessions': total_sessions,
                'attended_sessions': attended_sessions,
                'attendance_rate': attendance_rate,
                'avg_duration': avg_duration,
                'records': student_records
            })
            
        context = {
            'course': course,
            'student_attendance': student_attendance,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        # Add profile data to context
        if hasattr(user, 'profile'):
            context['profile'] = user.profile
        
        return render(request, 'website/attendance/print_report.html', context)
    else:
        # Filter by current user
        user_records = attendance_records.filter(user=user)
        
        # Group by video/module
        video_attendance = []
        for record in user_records:
            video_name = record.video.name if record.video else "جلسة مباشرة"
            module_name = record.module.name if record.module else ""
            
            video_attendance.append({
                'date': record.date,
                'video_name': video_name,
                'module_name': module_name,
                'is_present': record.is_present,
                'duration': record.duration,
            })
        
        # Calculate statistics
        total_sessions = user_records.count()
        attended_sessions = user_records.filter(is_present=True).count()
        
        if total_sessions > 0:
            attendance_rate = (attended_sessions / total_sessions) * 100
        else:
            attendance_rate = 0
            
        context = {
            'course': course,
            'video_attendance': video_attendance,
            'total_sessions': total_sessions,
            'attended_sessions': attended_sessions,
            'attendance_rate': attendance_rate,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        # Add profile data to context
        if hasattr(user, 'profile'):
            context['profile'] = user.profile
        
        return render(request, 'website/attendance/print_student_report.html', context)


@login_required
@require_POST
def create_live_session(request):
    """
    Create a live session and mark attendance for all enrolled students
    """
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST
    
    course_id = data.get('course_id')
    module_id = data.get('module_id')
    session_name = data.get('session_name')
    session_date_str = data.get('session_date')
    session_time_str = data.get('session_time')
    
    # Validate required fields
    if not course_id or not session_name or not session_date_str:
        return JsonResponse({
            'status': 'error',
            'message': 'يرجى تعبئة جميع الحقول المطلوبة'
        }, status=400)
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Check if user is the course teacher or a staff/admin
        if request.user != course.teacher and not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({
                'status': 'error',
                'message': 'يجب أن تكون مدرس الدورة لإنشاء جلسة مباشرة'
            }, status=403)
        
        # Get module if provided
        module = None
        if module_id:
            module = Module.objects.get(id=module_id, course=course)
        
        # Parse date and time
        session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
        
        # Create attendance records for all enrolled students
        students = course.enroller_user.all()
        attendance_records = []
        
        for student in students:
            # Check if attendance already exists for this student, course, and date
            existing = Attendance.objects.filter(
                user=student,
                course=course,
                date=session_date,
                video=None  # Live session has no video
            ).first()
            
            if not existing:
                attendance = Attendance.objects.create(
                    user=student,
                    course=course,
                    module=module,
                    date=session_date,
                    time_in=timezone.now(),
                    is_present=True,
                    notes=f"جلسة مباشرة: {session_name}"
                )
                attendance_records.append(attendance)
        
        return JsonResponse({
            'status': 'success',
            'message': f'تم إنشاء جلسة مباشرة وتسجيل حضور {len(attendance_records)} طالب',
            'records_created': len(attendance_records)
        })
        
    except Course.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'الدورة غير موجودة'
        }, status=404)
    except Module.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'الوحدة غير موجودة'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@login_required
@require_POST
def auto_attendance_tracking(request, video_id):
    """
    Automatically track attendance for video viewing
    """
    video = get_object_or_404(Video, id=video_id)
    user = request.user
    course = video.course
    
    # Check if user is enrolled in the course
    if user not in course.enroller_user.all():
        return JsonResponse({'status': 'error', 'message': 'يجب أن تكون مسجلاً في الدورة لتسجيل الحضور'}, status=403)
    
    # Check if attendance already recorded for today
    today = timezone.now().date()
    existing_attendance = Attendance.objects.filter(
        user=user,
        course=course,
        date=today,
        video=video
    ).first()
    
    if existing_attendance:
        # Return existing attendance record
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل الحضور مسبقاً',
            'attendance_id': existing_attendance.id
        })
    else:
        # Create new attendance record
        attendance = Attendance.objects.create(
            user=user,
            course=course,
            module=video.module,
            video=video,
            date=today,
            time_in=timezone.now(),
            is_present=True
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'تم تسجيل الحضور تلقائياً',
            'attendance_id': attendance.id
        })
