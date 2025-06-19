from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from user.models import Profile

def student_required(view_func):
    """
    Decorator للتأكد من أن المستخدم هو Student فقط
    يسمح فقط للمستخدمين الذين لديهم profile.status = 'Student'
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.status == 'Student':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'هذه العملية متاحة للطلاب فقط. لا يمكن للمعلمين أو الإداريين تنفيذ هذا الإجراء.')
                return redirect('dashboard')
        except Profile.DoesNotExist:
            messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم.')
            return redirect('dashboard')
    
    return _wrapped_view

def teacher_required(view_func):
    """
    Decorator للتأكد من أن المستخدم هو Teacher أو Admin
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.status in ['Teacher', 'Admin']:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'هذه العملية متاحة للمعلمين والإداريين فقط.')
                return redirect('dashboard')
        except Profile.DoesNotExist:
            messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم.')
            return redirect('dashboard')
    
    return _wrapped_view

def admin_required(view_func):
    """
    Decorator للتأكد من أن المستخدم هو Admin فقط
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.status == 'Admin':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'هذه العملية متاحة للإداريين فقط.')
                return redirect('dashboard')
        except Profile.DoesNotExist:
            messages.error(request, 'لم يتم العثور على ملف تعريف المستخدم.')
            return redirect('dashboard')
    
    return _wrapped_view 