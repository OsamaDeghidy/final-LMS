"""
Progress Helper Functions
يمكن استخدام هذه الدوال في Views لتتبع تقدم المستخدمين
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from website.models import Course, Module, UserProgress, ModuleProgress
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

def get_user_course_progress(user, course):
    """
    الحصول على تقدم المستخدم في الدورة
    """
    try:
        progress = UserProgress.objects.get(user=user, course=course)
        return {
            'overall_progress': progress.overall_progress,
            'is_completed': progress.is_completed,
            'enrolled_at': progress.enrolled_at,
            'last_accessed': progress.last_accessed,
            'completed_modules': ModuleProgress.objects.filter(
                user=user, module__course=course, is_completed=True
            ).count(),
            'total_modules': course.module_set.count()
        }
    except UserProgress.DoesNotExist:
        # إنشاء progress إذا لم يكن موجود
        progress = UserProgress.objects.create(user=user, course=course)
        return {
            'overall_progress': 0,
            'is_completed': False,
            'enrolled_at': progress.enrolled_at,
            'last_accessed': progress.last_accessed,
            'completed_modules': 0,
            'total_modules': course.module_set.count()
        }

def mark_content_viewed(user, module, content_type):
    """
    تسجيل مشاهدة محتوى معين
    content_type: 'video', 'pdf', 'note', 'quiz'
    """
    try:
        progress = ModuleProgress.get_or_create_progress(user, module)
        
        if content_type == 'video':
            progress.mark_video_watched()
        elif content_type == 'pdf':
            progress.mark_pdf_viewed()
        elif content_type == 'note':
            progress.mark_notes_read()
        elif content_type == 'quiz':
            progress.mark_quiz_completed()
        
        return {
            'success': True,
            'module_completed': progress.is_completed,
            'module_percentage': progress.get_completion_percentage(),
            'overall_progress': progress.module.course.get_user_progress_percentage(user)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@login_required
@require_http_methods(["POST"])
def track_progress_view(request):
    """
    View للتعامل مع AJAX requests لتتبع التقدم
    """
    try:
        data = json.loads(request.body)
        module_id = data.get('module_id')
        content_type = data.get('content_type')
        
        module = get_object_or_404(Module, id=module_id)
        
        # التحقق من أن المستخدم مسجل في الدورة
        if not module.course.is_user_enrolled(request.user):
            return JsonResponse({
                'success': False,
                'error': 'User not enrolled in this course'
            }, status=403)
        
        result = mark_content_viewed(request.user, module, content_type)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_dashboard_progress_data(user):
    """
    الحصول على بيانات التقدم للداشبورد
    """
    enrolled_courses = Course.objects.filter(enroller_user=user)
    progress_data = []
    
    for course in enrolled_courses:
        progress_info = get_user_course_progress(user, course)
        progress_data.append({
            'course': course,
            'progress': progress_info,
            'next_module': course.get_next_module_for_user(user)
        })
    
    return progress_data

def get_course_detailed_progress(user, course):
    """
    الحصول على تقدم مفصل للدورة
    """
    modules_progress = []
    
    for module in course.module_set.all().order_by('number'):
        try:
            progress = ModuleProgress.objects.get(user=user, module=module)
            module_data = {
                'module': module,
                'is_completed': progress.is_completed,
                'percentage': progress.get_completion_percentage(),
                'content_status': module.get_content_status_for_user(user),
                'last_accessed': progress.last_accessed
            }
        except ModuleProgress.DoesNotExist:
            module_data = {
                'module': module,
                'is_completed': False,
                'percentage': 0,
                'content_status': module.get_content_status_for_user(user),
                'last_accessed': None
            }
        
        modules_progress.append(module_data)
    
    overall_progress = get_user_course_progress(user, course)
    
    return {
        'course': course,
        'overall_progress': overall_progress,
        'modules': modules_progress
    }

# JavaScript Code للإدراج في Templates
PROGRESS_TRACKING_JS = """
<script>
function trackProgress(moduleId, contentType) {
    fetch('/track-progress/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            'module_id': moduleId,
            'content_type': contentType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث UI
            updateProgressBar(data.overall_progress);
            if (data.module_completed) {
                markModuleAsCompleted(moduleId);
            }
        } else {
            console.error('Progress tracking failed:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateProgressBar(percentage) {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.textContent = Math.round(percentage) + '%';
    }
}

function markModuleAsCompleted(moduleId) {
    const moduleElement = document.querySelector(`[data-module-id="${moduleId}"]`);
    if (moduleElement) {
        moduleElement.classList.add('completed');
    }
}

// تتبع مشاهدة الفيديو
function trackVideoProgress(videoElement, moduleId) {
    let hasTracked = false;
    
    videoElement.addEventListener('timeupdate', function() {
        if (!hasTracked && this.currentTime / this.duration > 0.8) {
            // إذا شاهد المستخدم 80% من الفيديو
            trackProgress(moduleId, 'video');
            hasTracked = true;
        }
    });
}

// تتبع قراءة PDF
function trackPDFView(moduleId) {
    // يمكن تتبع فتح PDF فوراً أو بعد وقت معين
    setTimeout(() => {
        trackProgress(moduleId, 'pdf');
    }, 5000); // بعد 5 ثواني من فتح PDF
}

// تتبع قراءة الملاحظات
function trackNotesRead(moduleId) {
    trackProgress(moduleId, 'note');
}
</script>
""" 