from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Meeting, Participant, Notification
from .forms import MeetingForm, MeetingFilterForm

@login_required
def meeting_list(request):
    """View for listing all meetings"""
    form = MeetingFilterForm(request.GET)
    meetings = Meeting.objects.all()
    
    # School filtering removed
    
    # Apply filters if form is valid
    if form.is_valid():
        if form.cleaned_data.get('meeting_type'):
            meetings = meetings.filter(meeting_type=form.cleaned_data['meeting_type'])
        if form.cleaned_data.get('start_date'):
            meetings = meetings.filter(start_time__date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            meetings = meetings.filter(start_time__date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('is_past') is not None:
            if form.cleaned_data['is_past']:
                meetings = meetings.filter(start_time__lt=timezone.now())
            else:
                meetings = meetings.filter(start_time__gte=timezone.now())
    
    # Paginate results
    paginator = Paginator(meetings.order_by('-start_time'), 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get user profile and student data
    profile = None
    student = None
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        if hasattr(profile, 'student'):
            student = profile.student
            
    context = {
        'page_obj': page_obj,
        'form': form,
        'active_tab': 'meetings',
        'profile': profile,
        'student': student,
    }
    return render(request, 'website/meetings/meeting_list.html', context)

@login_required
def meeting_detail(request, pk):
    """View for displaying meeting details"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # School access check removed
    
    # Get participant status for current user
    user_participant = Participant.objects.filter(meeting=meeting, user=request.user).first()
    
    # Get all participants
    participants = meeting.participant_set.all().select_related('user')
    
    # Get user profile if it exists
    profile = None
    student = None
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        # Get student info if available
        if hasattr(profile, 'student'):
            student = profile.student
    
    context = {
        'meeting': meeting,
        'user_participant': user_participant,
        'participants': participants,
        'active_tab': 'meetings',
        'profile': profile,
        'student': student,
    }
    return render(request, 'website/meetings/meeting_detail.html', context)

@login_required
def meeting_create(request):
    """View for creating a new meeting"""
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.creator = request.user
            
            # Set school based on user's profile if available
            if hasattr(request.user, 'profile'):
                # Check if the user is a teacher and has an organization
                if hasattr(request.user.profile, 'teacher') and request.user.profile.teacher:
                    teacher = request.user.profile.teacher
                    if hasattr(teacher, 'organization') and teacher.organization:
                        meeting.school = teacher.organization
            
            meeting.save()
            messages.success(request, "تم إنشاء الاجتماع بنجاح")
            return redirect('meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm()
    
    # Get user profile and student data
    profile = None
    student = None
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        if hasattr(profile, 'student'):
            student = profile.student
    
    context = {
        'form': form,
        'active_tab': 'meetings',
        'is_create': True,
        'profile': profile,
        'student': student,
    }
    return render(request, 'website/meetings/meeting_form.html', context)

@login_required
def meeting_update(request, pk):
    """View for updating an existing meeting"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user has permission to edit
    if meeting.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("ليس لديك صلاحية لتعديل هذا الاجتماع")
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES, instance=meeting)
        if form.is_valid():
            updated_meeting = form.save()
            
            # If meeting was rescheduled, create notification
            if 'start_time' in form.changed_data:
                Notification.create_for_meeting(
                    meeting=updated_meeting,
                    notification_type='RESCHEDULED',
                    message=f"تم إعادة جدولة الاجتماع {updated_meeting.title} إلى {updated_meeting.start_time.strftime('%Y-%m-%d %H:%M')}",
                    scheduled_time=timezone.now()
                )
            
            messages.success(request, "تم تحديث الاجتماع بنجاح")
            return redirect('meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(instance=meeting)
    
    context = {
        'form': form,
        'meeting': meeting,
        'active_tab': 'meetings',
        'is_create': False,
    }
    return render(request, 'website/meetings/meeting_form.html', context)

@login_required
def meeting_delete(request, pk):
    """View for deleting a meeting"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user has permission to delete
    if meeting.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("ليس لديك صلاحية لحذف هذا الاجتماع")
    
    if request.method == 'POST':
        # Create cancellation notification
        Notification.create_for_meeting(
            meeting=meeting,
            notification_type='CANCELLED',
            message=f"تم إلغاء الاجتماع {meeting.title}",
            scheduled_time=timezone.now()
        )
        
        meeting.is_active = False
        meeting.save()
        messages.success(request, "تم إلغاء الاجتماع بنجاح")
        return redirect('meeting_list')
    
    context = {
        'meeting': meeting,
        'active_tab': 'meetings',
    }
    return render(request, 'website/meetings/meeting_confirm_delete.html', context)

@login_required
@require_POST
def mark_attendance(request, pk):
    """API view for marking attendance"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if meeting is ongoing
    if not meeting.is_ongoing:
        return JsonResponse({'status': 'error', 'message': 'الاجتماع غير متاح للحضور حالياً'}, status=400)
    
    # Get or create participant
    participant, created = Participant.objects.get_or_create(
        meeting=meeting,
        user=request.user
    )
    
    # Mark attendance
    participant.mark_attendance()
    
    return JsonResponse({
        'status': 'success',
        'message': 'تم تسجيل حضورك بنجاح',
        'attendance_time': participant.attendance_time.strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required
@require_POST
def mark_exit(request, pk):
    """API view for marking exit"""
    meeting = get_object_or_404(Meeting, pk=pk)
    participant = get_object_or_404(Participant, meeting=meeting, user=request.user)
    
    # Mark exit
    participant.mark_exit()
    
    return JsonResponse({
        'status': 'success',
        'message': 'تم تسجيل مغادرتك بنجاح',
        'exit_time': participant.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': str(participant.attendance_duration)
    })

@login_required
def my_meetings(request):
    """View for displaying user's meetings"""
    # Get meetings where user is creator or participant
    created_meetings = Meeting.objects.filter(creator=request.user)
    participating_meetings = Meeting.objects.filter(participant__user=request.user)
    
    # Combine and remove duplicates
    meetings = (created_meetings | participating_meetings).distinct()
    
    # Filter by upcoming/past
    filter_type = request.GET.get('filter', 'upcoming')
    if filter_type == 'upcoming':
        meetings = meetings.filter(start_time__gte=timezone.now())
    elif filter_type == 'past':
        meetings = meetings.filter(start_time__lt=timezone.now())
    
    # Paginate results
    paginator = Paginator(meetings.order_by('-start_time'), 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'active_tab': 'my_meetings',
    }
    return render(request, 'website/meetings/my_meetings.html', context)

@login_required
def notifications(request):
    """View for displaying user's notifications"""
    notifications = Notification.objects.filter(
        recipients=request.user
    ).order_by('-scheduled_time')
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, recipients=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
    
    # Paginate results
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_tab': 'notifications',
    }
    return render(request, 'website/meetings/notifications.html', context)
