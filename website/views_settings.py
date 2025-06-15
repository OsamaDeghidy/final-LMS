from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
import os
import json

from .forms import CustomPasswordChangeForm, ProfileUpdateForm, CertificateTemplateForm
from .models import CertificateTemplate
from user.models import Profile


@login_required
def settings_view(request):
    """صفحة الإعدادات الرئيسية مع 3 تبويبات"""
    # Get user profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        Profile.objects.create(user=request.user, name=request.user.username)
        profile = request.user.profile
    
    # Get certificate templates if user is admin or teacher
    certificate_templates = []
    user_templates = []
    show_certificate_tab = False
    
    if profile.is_teacher_or_admin():
        show_certificate_tab = True
        certificate_templates = CertificateTemplate.objects.filter(is_active=True)
        user_templates = CertificateTemplate.objects.filter(created_by=request.user, is_active=True)
    
    context = {
        'profile': profile,
        'show_certificate_tab': show_certificate_tab,
        'certificate_templates': certificate_templates,
        'user_templates': user_templates,
        'password_form': CustomPasswordChangeForm(request.user),
        'profile_form': ProfileUpdateForm(instance=profile),
        'certificate_form': CertificateTemplateForm(),
    }
    
    return render(request, 'website/settings.html', context)


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """تغيير كلمة المرور"""
    form = CustomPasswordChangeForm(request.user, request.POST)
    
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # Keep user logged in
        messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
        return JsonResponse({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح!'
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list
        
        return JsonResponse({
            'success': False,
            'errors': errors
        })


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """تحديث الملف الشخصي"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        Profile.objects.create(user=request.user, name=request.user.username)
        profile = request.user.profile
    
    form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
    
    if form.is_valid():
        # Update user's email if changed
        if form.cleaned_data.get('email') and form.cleaned_data['email'] != request.user.email:
            request.user.email = form.cleaned_data['email']
            request.user.save()
        
        form.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح!')
        
        return JsonResponse({
            'success': True,
            'message': 'تم تحديث الملف الشخصي بنجاح!'
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list
        
        return JsonResponse({
            'success': False,
            'errors': errors
        })


@login_required
@require_http_methods(["POST"])
def save_certificate_template(request):
    """حفظ قالب الشهادة (للمدراء والمعلمين فقط)"""
    # Check permissions
    try:
        profile = request.user.profile
        if not profile.is_teacher_or_admin():
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية لإنشاء قوالب الشهادات'
            })
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'الملف الشخصي غير موجود'
        })
    
    form = CertificateTemplateForm(request.POST, request.FILES)
    
    if form.is_valid():
        # Create certificate template
        template = CertificateTemplate(
            created_by=request.user,
            template_name=f"قالب {request.user.profile.name} - {form.cleaned_data['template_style']}",
            template_style=form.cleaned_data['template_style'],
            primary_color=form.cleaned_data['primary_color'],
            institution_name=form.cleaned_data['institution_name'],
            signature_name=form.cleaned_data['signature_name'],
            signature_title=form.cleaned_data['signature_title'],
            certificate_text=form.cleaned_data['certificate_text'],
            include_qr_code=form.cleaned_data['include_qr_code'],
            include_grade=form.cleaned_data['include_grade'],
        )
        
        # Handle file uploads
        if form.cleaned_data.get('institution_logo'):
            template.institution_logo = form.cleaned_data['institution_logo']
        
        if form.cleaned_data.get('signature_image'):
            template.signature_image = form.cleaned_data['signature_image']
        
        template.save()
        
        messages.success(request, 'تم حفظ قالب الشهادة بنجاح!')
        
        return JsonResponse({
            'success': True,
            'message': 'تم حفظ قالب الشهادة بنجاح!',
            'template_id': template.id
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list
        
        return JsonResponse({
            'success': False,
            'errors': errors
        })


@login_required
@require_http_methods(["POST"])
def set_default_template(request, template_id):
    """تعيين قالب كافتراضي"""
    try:
        profile = request.user.profile
        if not profile.is_teacher_or_admin():
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية لتعديل قوالب الشهادات'
            })
        
        template = get_object_or_404(CertificateTemplate, id=template_id, created_by=request.user)
        
        # Remove default from all other templates
        CertificateTemplate.objects.filter(created_by=request.user).update(is_default=False)
        
        # Set this template as default
        template.is_default = True
        template.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم تعيين القالب كافتراضي بنجاح!'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'الملف الشخصي غير موجود'
        })


@login_required
@require_http_methods(["POST"])
def delete_template(request, template_id):
    """حذف قالب الشهادة"""
    try:
        profile = request.user.profile
        if not profile.is_teacher_or_admin():
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية لحذف قوالب الشهادات'
            })
        
        template = get_object_or_404(CertificateTemplate, id=template_id, created_by=request.user)
        
        # Delete associated files
        if template.institution_logo:
            if default_storage.exists(template.institution_logo.name):
                default_storage.delete(template.institution_logo.name)
        
        if template.signature_image:
            if default_storage.exists(template.signature_image.name):
                default_storage.delete(template.signature_image.name)
        
        template.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'تم حذف القالب بنجاح!'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'الملف الشخصي غير موجود'
        })


@login_required
def preview_certificate(request, template_id):
    """معاينة قالب الشهادة"""
    try:
        profile = request.user.profile
        if not profile.is_teacher_or_admin():
            messages.error(request, 'ليس لديك صلاحية لمعاينة قوالب الشهادات')
            return redirect('settings')
        
        template = get_object_or_404(CertificateTemplate, id=template_id, created_by=request.user)
        
        # Sample data for preview
        sample_data = {
            'student_name': 'أحمد محمد علي',
            'course_name': 'دورة تطوير المواقع الإلكترونية',
            'completion_date': '2024-12-25',
            'grade': '95%' if template.include_grade else None
        }
        
        # Format certificate text with sample data
        formatted_text = template.format_certificate_text(
            sample_data['student_name'],
            sample_data['course_name'],
            sample_data['completion_date'],
            sample_data['grade']
        )
        
        context = {
            'template': template,
            'sample_data': sample_data,
            'formatted_certificate_text': formatted_text,
            'preview': True,
            'profile': profile
        }
        
        return render(request, 'website/certificate_preview.html', context)
        
    except Profile.DoesNotExist:
        messages.error(request, 'الملف الشخصي غير موجود')
        return redirect('settings') 