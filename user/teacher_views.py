import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import os
from .models import TeacherApplication, Profile

logger = logging.getLogger(__name__)

@login_required
def make_teacher(request):
    logger.info(f"make_teacher view called with method: {request.method}")
    logger.info(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
    
    if request.method == 'GET':
        # Handle GET request - show the form
        if hasattr(request.user, 'teacher'):
            messages.info(request, 'أنت بالفعل معلم في النظام')
            return redirect('dashboard')
            
        if TeacherApplication.objects.filter(profile=request.user.profile, status='pending').exists():
            messages.info(request, 'لديك طلب قيد المراجعة بالفعل')
            return redirect('dashboard')
            
        return redirect('dashboard')
    
    # Handle POST request
    try:
        logger.info(f"Processing POST request data: {request.POST}")
        logger.info(f"Files in request: {request.FILES}")
        
        # Check if user is already a teacher
        if hasattr(request.user, 'teacher'):
            messages.warning(request, 'أنت بالفعل معلم في النظام')
            return redirect('dashboard')
            
        # Get form data with proper error handling
        try:
            profile = request.user.profile
            bio = request.POST.get('bio', '').strip()
            specialization = request.POST.get('specialization', '').strip()
            cv_file = request.FILES.get('cv')
            
            logger.info(f"Form data - Bio: {bio}, Specialization: {specialization}, CV: {'present' if cv_file else 'not provided'}")
            
            # Validate required fields
            if not all([bio, specialization]):
                messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة')
                return redirect('dashboard')
                
            # Check for existing pending application
            if TeacherApplication.objects.filter(profile=profile, status='pending').exists():
                messages.info(request, 'لديك طلب قيد المراجعة بالفعل')
                return redirect('dashboard')
                
            # Create teacher application
            teacher_application = TeacherApplication(
                profile=profile,
                bio=bio,
                specialization=specialization,
                status='pending'
            )
            
            # Save the application first to get an ID
            teacher_application.save()
            logger.info(f"Created teacher application with ID: {teacher_application.id}")
            
            # Handle file upload if present
            if cv_file:
                try:
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join(settings.MEDIA_ROOT, 'teacher_applications', 'cvs')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate a unique filename
                    filename = f"{teacher_application.id}_{cv_file.name}"
                    file_path = os.path.join('teacher_applications', 'cvs', filename)
                    
                    # Save the file
                    file_content = cv_file.read()
                    saved_path = default_storage.save(file_path, ContentFile(file_content))
                    
                    # Update the application with the file path
                    teacher_application.cv = saved_path
                    teacher_application.save()
                    logger.info(f"Saved CV file to: {saved_path}")
                    
                except Exception as file_error:
                    logger.error(f"Error saving CV file: {str(file_error)}")
                    # Don't fail the whole request if file save fails
                    messages.warning(request, 'تم حفظ الطلب مع ملاحظة: حدث خطأ في حفظ الملف المرفق')
            
            messages.success(request, 'تم إرسال طلبك بنجاح. سيتم مراجعته من قبل الإدارة')
            logger.info(f"Successfully created teacher application: {teacher_application.id}")
            return redirect('dashboard')
            
        except Exception as form_error:
            logger.error(f"Form processing error: {str(form_error)}", exc_info=True)
            messages.error(request, f'حدث خطأ أثناء معالجة النموذج: {str(form_error)}')
            return redirect('dashboard')
            
    except Exception as e:
        logger.error(f"Unexpected error in make_teacher: {str(e)}", exc_info=True)
        messages.error(request, 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.')
        return redirect('dashboard')
