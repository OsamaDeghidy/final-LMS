from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import uuid
from django.utils import timezone
from user.models import Profile, Organization, Teacher, Student
from moviepy.editor import *
import subprocess
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
#from django.core.files.storage import default_storage as storage
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'


class Tags(models.Model):
    name=models.CharField(max_length=2000,blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'مبتدئ'),
        ('intermediate', 'متوسط'),
        ('advanced', 'متقدم'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('published', 'منشور'),
        ('draft', 'مسودة'),
    ]
    
    name = models.CharField(max_length=2000,blank=True,null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null = True, blank = True)
    teacher=models.ForeignKey(Teacher,on_delete=models.CASCADE, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner', blank=True, null=True)
    enroller_user=models.ManyToManyField(User,blank=True)
    tags=models.ManyToManyField(Tags, blank=True)
    description=RichTextField(null=True, blank=True)
    image_course=models.ImageField(null=True, blank=True, default='blank_course.png',upload_to='course/')
    price = models.DecimalField(null=True, blank=True, default=0, max_digits=100, decimal_places=2)
    small_description = models.TextField(null=True, blank=True)
    learned = RichTextField(null = True, blank = True)
    created_at=models.DateTimeField(null=True, blank = True)
    updated_at=models.DateTimeField(null=True, blank =True)
    rating=models.FloatField(null=True, blank = True, default=0)
    total_video=models.IntegerField(null=True, blank = True)
    vidoes_time=models.CharField(max_length=2000,null=True, blank = True)
    total_module=models.IntegerField(blank=True, null=True, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    syllabus_pdf = models.FileField(upload_to='course_pdfs/syllabus/', null=True, blank=True, help_text='Upload course syllabus PDF')
    materials_pdf = models.FileField(upload_to='course_pdfs/materials/', null=True, blank=True, help_text='Upload additional course materials PDF')
    
    def save(self, *args, **kwargs):
        # First save the course if it's a new instance
        super().save(*args, **kwargs)
        
    def get_user_progress(self, user):
        """Get user's progress in this course"""
        try:
            return UserProgress.objects.get(user=user, course=self)
        except UserProgress.DoesNotExist:
            # Create progress if doesn't exist
            return UserProgress.objects.create(user=user, course=self)
    
    def get_user_progress_percentage(self, user):
        """Get user's progress percentage in this course"""
        progress = self.get_user_progress(user)
        return progress.overall_progress
    
    def is_user_enrolled(self, user):
        """Check if user is enrolled in this course"""
        return self.enroller_user.filter(id=user.id).exists()
    
    def get_modules_with_progress(self, user):
        """Get all modules with user's progress"""
        modules = self.module_set.all().order_by('number')
        modules_with_progress = []
        
        for module in modules:
            try:
                progress = ModuleProgress.objects.get(user=user, module=module)
            except ModuleProgress.DoesNotExist:
                progress = None
            
            modules_with_progress.append({
                'module': module,
                'progress': progress,
                'completed': progress.is_completed if progress else False,
                'percentage': progress.get_completion_percentage() if progress else 0
            })
        
        return modules_with_progress
    
    def get_next_module_for_user(self, user):
        """Get the next incomplete module for the user"""
        modules = self.module_set.all().order_by('number')
        
        for module in modules:
            try:
                progress = ModuleProgress.objects.get(user=user, module=module)
                if not progress.is_completed:
                    return module
            except ModuleProgress.DoesNotExist:
                # Return first module without progress
                return module
        
        return None  # All modules completed
    
    @property
    def final_exam(self):
        """Get the final exam for this course"""
        return self.exams.filter(is_final=True, is_active=True).first()
    
    def __str__(self):
        return self.name



class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    course = models.ForeignKey(Course, related_name="enrollments", on_delete=models.CASCADE)
    student = models.ForeignKey(User, related_name="user_courses", on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('course', 'student')

    def save(self, *args, **kwargs):
        # Update the course's enrolled users count
        if not self.pk:  # If this is a new enrollment
            self.course.enroller_user.add(self.student)
            
        super().save(*args, **kwargs)
        
        # Create UserProgress if this is a new enrollment
        if not self.pk or not hasattr(self, '_user_progress_created'):
            try:
                user_progress, created = UserProgress.objects.get_or_create(
                    user=self.student,
                    course=self.course
                )
                if created:
                    self._user_progress_created = True
            except Exception as e:
                print(f"Error creating UserProgress: {e}")

    def __str__(self):
        return f"{self.course.name} - {self.student.username}"


class Module(models.Model):
    name = models.CharField(max_length=2000, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    number = models.IntegerField(null=True, blank=True)
    description = RichTextField(null=True, blank=True)
    # Each module has exactly one video
    video = models.FileField(upload_to='module_videos/', null=True, blank=True)
    video_duration = models.IntegerField(default=0)
    # Each module has exactly one PDF
    pdf = models.FileField(upload_to='module_pdfs/', null=True, blank=True)
    # Each module has exactly one note
    note = RichTextField(null=True, blank=True)
    # Quiz will be linked via foreign key from Quiz model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['number']
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
    
    def save(self, *args, **kwargs):
        # If this is a new module or the video file has been updated
        if not self.pk or 'video' in [f.name for f in self._meta.get_fields() if f.name == 'video']:
            if self.video:
                try:
                    # Get video duration using moviepy
                    clip = VideoFileClip(self.video.path)
                    self.video_duration = int(clip.duration)
                    clip.close()
                except Exception as e:
                    print(f"Error processing video: {e}")
                    self.video_duration = 0
        
        # If this is a new module, set the module number
        if not self.pk:
            # Get the highest module number for this course and add 1
            last_module = Module.objects.filter(course=self.course).order_by('-number').first()
            self.number = last_module.number + 1 if last_module else 1
            
        super().save(*args, **kwargs)
        
        # Update course duration after saving module
        if self.course:
            self.course.save()
            
    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.video:
            if os.path.isfile(self.video.path):
                os.remove(self.video.path)
        if self.pdf:
            if os.path.isfile(self.pdf.path):
                os.remove(self.pdf.path)
        super().delete(*args, **kwargs)
    
    def get_user_progress(self, user):
        """Get user's progress for this module"""
        return ModuleProgress.get_or_create_progress(user, self)
    
    def mark_content_as_viewed(self, user, content_type):
        """Mark specific content as viewed for user"""
        progress = self.get_user_progress(user)
        
        if content_type == 'video':
            progress.mark_video_watched()
        elif content_type == 'pdf':
            progress.mark_pdf_viewed()
        elif content_type == 'note':
            progress.mark_notes_read()
        elif content_type == 'quiz':
            progress.mark_quiz_completed()
    
    def is_completed_by_user(self, user):
        """Check if this module is completed by the user"""
        try:
            progress = ModuleProgress.objects.get(user=user, module=self)
            return progress.is_completed
        except ModuleProgress.DoesNotExist:
            return False
    
    def get_completion_percentage_for_user(self, user):
        """Get completion percentage for this module for specific user"""
        try:
            progress = ModuleProgress.objects.get(user=user, module=self)
            return progress.get_completion_percentage()
        except ModuleProgress.DoesNotExist:
            return 0
    
    def has_content(self):
        """Check if module has any content"""
        return any([self.video, self.pdf, self.note, self.module_quizzes.filter(is_active=True).exists()])
    
    def get_content_status_for_user(self, user):
        """Get detailed content status for user"""
        progress = self.get_user_progress(user)
        
        return {
            'video': {
                'exists': bool(self.video),
                'completed': progress.video_watched,
                'url': self.video.url if self.video else None,
                'duration': self.video_duration
            },
            'pdf': {
                'exists': bool(self.pdf),
                'completed': progress.pdf_viewed,
                'url': self.pdf.url if self.pdf else None
            },
            'note': {
                'exists': bool(self.note),
                'completed': progress.notes_read,
                'content': self.note
            },
            'quiz': {
                'exists': self.module_quizzes.filter(is_active=True).exists(),
                'completed': progress.quiz_completed,
                'quizzes': list(self.module_quizzes.filter(is_active=True))
            },
            'overall_completed': progress.is_completed,
            'completion_percentage': progress.get_completion_percentage()
        }
    
    def get_ordered_content(self):
        """
        Returns all content for this module in a structured order:
        1. Video (if exists)
        2. PDF (if exists) 
        3. Notes (if exists)
        4. Quizzes (related to this module)
        5. Assignments (related to this module)
        """
        content_items = []
        
        # 1. Add video if exists
        if self.video:
            content_items.append({
                'type': 'video',
                'id': self.id,  # استخدام ID الوحدة مباشرة
                'name': f'فيديو: {self.name}',
                'duration': self.video_duration if self.video_duration else 0,
                'url': self.video.url,
                'order': 1,
                'module_id': self.id
            })
        
        # 2. Add PDF if exists
        if self.pdf:
            content_items.append({
                'type': 'pdf',
                'id': self.id,  # استخدام ID الوحدة مباشرة
                'name': f'ملف PDF: {self.name}',
                'url': self.pdf.url,
                'order': 2,
                'module_id': self.id
            })
        
        # 3. Add notes if exists
        if self.note:
            content_items.append({
                'type': 'note',
                'id': self.id,  # استخدام ID الوحدة مباشرة
                'name': f'ملاحظات: {self.name}',
                'content': self.note,
                'order': 3,
                'module_id': self.id
            })
        
        # 4. Add quizzes related to this module
        quizzes = self.module_quizzes.filter(is_active=True).order_by('created_at')
        for quiz in quizzes:
            content_items.append({
                'type': 'quiz',
                'id': quiz.id,
                'name': quiz.title or f'اختبار: {self.name}',
                'description': quiz.description,
                'time_limit': quiz.time_limit,
                'questions_count': quiz.questions.count(),
                'order': 4,
                'module_id': self.id,
                'quiz_object': quiz
            })
        
        # 5. Add assignments related to this module
        assignments = self.module_assignments.filter(is_active=True).order_by('created_at')
        for assignment in assignments:
            content_items.append({
                'type': 'assignment',
                'id': assignment.id,
                'name': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date,
                'points': assignment.points,
                'order': 5,
                'module_id': self.id,
                'assignment_object': assignment
            })
        
        # Sort by order and return
        return sorted(content_items, key=lambda x: x['order'])


class CourseReview(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = RichTextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'user']
        ordering = ['-created_at']
        verbose_name = 'Course Review'
        verbose_name_plural = 'Course Reviews'
    
    def __str__(self):
        return f"{self.user.username}'s review of {self.course.name} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update course average rating
        course = self.course
        avg_rating = CourseReview.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
        course.rating = round(avg_rating, 1) if avg_rating else 0
        course.save()


class ReviewReply(models.Model):
    review = models.ForeignKey(CourseReview, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply_text = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Review Reply'
        verbose_name_plural = 'Review Replies'
    
    def __str__(self):
        return f"Reply by {self.user.username} to {self.review.user.username}'s review"


class UserProgress(models.Model):
    """Tracks user's overall progress in a course"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    overall_progress = models.FloatField(default=0)  # 0-100%

    class Meta:
        unique_together = ('user', 'course')
        verbose_name_plural = 'User Progress'

    def update_progress(self):
        """Update overall progress based on module completion"""
        total_modules = self.course.module_set.count()
        if total_modules == 0:
            self.overall_progress = 0
            return

        completed_modules = ModuleProgress.objects.filter(
            user=self.user,
            module__course=self.course,
            is_completed=True
        ).count()
        
        self.overall_progress = (completed_modules / total_modules) * 100
        self.is_completed = self.overall_progress >= 100
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.course.name} ({self.overall_progress}%)"


class ModuleProgress(models.Model):
    """Tracks user's progress within a specific module"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey('Module', on_delete=models.CASCADE, related_name='user_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    video_watched = models.BooleanField(default=False)
    pdf_viewed = models.BooleanField(default=False)
    notes_read = models.BooleanField(default=False)
    quiz_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'module')
        verbose_name_plural = 'Module Progress'

    def save(self, *args, **kwargs):
        # Check if module is completed based on available content
        # Only count components that actually exist
        required_components = []
        
        if self.module.video:
            required_components.append(self.video_watched)
        if self.module.pdf:
            required_components.append(self.pdf_viewed)
        if self.module.note:
            required_components.append(self.notes_read)
        
        # Check if there are active quizzes for this module
        has_quiz = self.module.module_quizzes.filter(is_active=True).exists()
        if has_quiz:
            required_components.append(self.quiz_completed)
        
        # Module is completed if all available components are completed
        # If no components exist, consider it completed
        if required_components:
            self.is_completed = all(required_components)
        else:
            self.is_completed = True
        
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update parent UserProgress
        try:
            user_progress, created = UserProgress.objects.get_or_create(
                user=self.user,
                course=self.module.course
            )
            user_progress.update_progress()
        except Exception as e:
            print(f"Error updating UserProgress: {e}")

    def mark_video_watched(self):
        """Mark video as watched"""
        if not self.video_watched:
            self.video_watched = True
            self.save()

    def mark_pdf_viewed(self):
        """Mark PDF as viewed"""
        if not self.pdf_viewed:
            self.pdf_viewed = True
            self.save()

    def mark_notes_read(self):
        """Mark notes as read"""
        if not self.notes_read:
            self.notes_read = True
            self.save()

    def mark_quiz_completed(self):
        """Mark quiz as completed"""
        if not self.quiz_completed:
            self.quiz_completed = True
            self.save()

    @classmethod
    def get_or_create_progress(cls, user, module):
        """Get or create progress for a user and module"""
        progress, created = cls.objects.get_or_create(
            user=user,
            module=module
        )
        return progress

    def get_completion_percentage(self):
        """Get completion percentage for this module"""
        total_components = 0
        completed_components = 0
        
        if self.module.video:
            total_components += 1
            if self.video_watched:
                completed_components += 1
        
        if self.module.pdf:
            total_components += 1
            if self.pdf_viewed:
                completed_components += 1
        
        if self.module.note:
            total_components += 1
            if self.notes_read:
                completed_components += 1
        
        if self.module.module_quizzes.filter(is_active=True).exists():
            total_components += 1
            if self.quiz_completed:
                completed_components += 1
        
        if total_components == 0:
            return 100
        
        return (completed_components / total_components) * 100

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} - {self.module.name} ({status})"


class CourseProgress(models.Model):
    """Aggregated statistics for a course"""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='progress_stats')
    total_enrollments = models.PositiveIntegerField(default=0)
    active_learners = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0)  # 0-100%
    average_progress = models.FloatField(default=0)  # 0-100%
    last_updated = models.DateTimeField(auto_now=True)

    def update_statistics(self):
        """Update all statistics for the course"""
        from django.db.models import Avg, Count, F, Q
        
        # Get all user progress for this course
        progress_data = UserProgress.objects.filter(course=self.course).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_completed=False)),
            avg_progress=Avg('overall_progress')
        )
        
        self.total_enrollments = progress_data['total'] or 0
        self.active_learners = progress_data['active'] or 0
        self.average_progress = progress_data['avg_progress'] or 0
        
        # Calculate completion rate
        completed = UserProgress.objects.filter(
            course=self.course,
            is_completed=True
        ).count()
        
        self.completion_rate = (completed / self.total_enrollments * 100) if self.total_enrollments > 0 else 0
        self.save()

    @classmethod
    def update_for_course(cls, course):
        """Update statistics for a specific course"""
        progress, created = cls.objects.get_or_create(course=course)
        progress.update_statistics()
        return progress

    def __str__(self):
        return f"Stats for {self.course.name} - {self.completion_rate}% completion"


class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ('video', 'فيديو كويز'),
        ('module', 'كويز وحدة'),
        ('quick', 'كويز سريع'),
    ]
    
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='module_quizzes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='course_quizzes')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPE_CHOICES, default='video')
    start_time = models.DurationField(default=timedelta(seconds=0), null=True, blank=True)
    time_limit = models.PositiveIntegerField(help_text='Time limit in minutes', null=True, blank=True)
    pass_mark = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        if self.title:
            return self.title
        elif self.video:
            return f"كويز للفيديو: {self.video.name}"
        elif self.module:
            return f"كويز للوحدة: {self.module.name}"
        else:
            return f"كويز {self.id}"


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'اختيار من متعدد'),
        ('true_false', 'صح أو خطأ'),
        ('short_answer', 'إجابة قصيرة'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=1000)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(null=True, blank=True, help_text='شرح الإجابة الصحيحة')
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for {self.content_object}"

class Certification(models.Model):
    user = models.ForeignKey(User, related_name='user_certifications', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    attachments = GenericRelation(Attachment)
    issuing_organization = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=255, blank=True)
    credential_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tags, related_name='certifications', blank=True)
    certificate_image = models.ImageField(upload_to='certificates/', blank=True)
    verification_status = models.BooleanField(default=False)
    related_courses = models.ManyToManyField(Course, related_name='course_certifications', blank=True)
    completion_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    is_auto_generated = models.BooleanField(default=True, help_text='تم إنشاؤها تلقائيًا بعد إكمال الدورة')

    def __str__(self):
        return f"{self.name} - {self.user.profile.name if hasattr(self.user, 'profile') else self.user.username}"


class Exam(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='module_exams')
    description = RichTextField(null=True, blank=True)
    time_limit = models.PositiveIntegerField(help_text='وقت الامتحان بالدقائق', null=True, blank=True)
    pass_mark = models.FloatField(default=60.0, help_text='النسبة المئوية للنجاح')
    is_final = models.BooleanField(default=False, help_text='هل هذا امتحان نهائي للدورة؟')
    total_points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    allow_multiple_attempts = models.BooleanField(default=False)
    max_attempts = models.PositiveIntegerField(default=1)
    show_answers_after = models.BooleanField(default=False, help_text='إظهار الإجابات الصحيحة بعد الانتهاء')
    randomize_questions = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"


class ExamQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'اختيار من متعدد'),
        ('true_false', 'صح أو خطأ'),
        ('short_answer', 'إجابة قصيرة'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(null=True, blank=True, help_text='شرح الإجابة الصحيحة')
    image = models.ImageField(upload_to='exam_question_images/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.text[:50]}..."


class ExamAnswer(models.Model):
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.text


class UserExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['user', 'exam', 'attempt_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - محاولة {self.attempt_number}"
    
    def calculate_score(self):
        # حساب النتيجة بناءً على الإجابات
        total_points = sum(q.points for q in self.exam.questions.all())
        earned_points = sum(a.question.points for a in self.answers.filter(is_correct=True))
        
        if total_points > 0:
            self.score = (earned_points / total_points) * 100
        else:
            self.score = 0
            
        self.passed = self.score >= self.exam.pass_mark
        self.save()


class UserExamAnswer(models.Model):
    attempt = models.ForeignKey(UserExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(ExamAnswer, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)  # للأسئلة ذات الإجابات القصيرة
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(default=0)
    
    def __str__(self):
        return f"إجابة {self.attempt.user.username} على سؤال {self.question.id}"


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='module_assignments')
    description = RichTextField()
    attachments = GenericRelation(Attachment)
    due_date = models.DateTimeField(null=True, blank=True)
    points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    allow_late_submissions = models.BooleanField(default=False)
    late_submission_penalty = models.FloatField(default=0, help_text='نسبة الخصم للتسليم المتأخر')
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'تم التسليم'),
        ('graded', 'تم التقييم'),
        ('returned', 'تم الإعادة للتعديل'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    attachments = GenericRelation(Attachment)
    submission_text = RichTextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    grade = models.FloatField(null=True, blank=True)
    feedback = RichTextField(null=True, blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # إذا كان هذا إنشاء جديد
            if self.assignment.due_date and timezone.now() > self.assignment.due_date:
                self.is_late = True
        super().save(*args, **kwargs)


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_records')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField(default=timezone.now)
    time_out = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_present = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'course', 'date', 'module']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.name} - {self.date}"
    
    def save(self, *args, **kwargs):
        if self.time_out and self.time_in:
            self.duration = self.time_out - self.time_in
        super().save(*args, **kwargs)


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['user', 'quiz', 'attempt_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title if self.quiz.title else f'Quiz {self.quiz.id}'} - محاولة {self.attempt_number}"
    
    def calculate_score(self):
        total_points = sum(q.points for q in self.quiz.questions.all())
        earned_points = sum(a.question.points for a in self.answers.filter(is_correct=True))
        
        if total_points > 0:
            self.score = (earned_points / total_points) * 100
        else:
            self.score = 0
            
        self.passed = self.score >= self.quiz.pass_mark
        self.save()


class QuizUserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)  # للأسئلة ذات الإجابات القصيرة
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(default=0)
    
    def __str__(self):
        return f"إجابة {self.attempt.user.username} على سؤال {self.question.id}"


class Meeting(models.Model):
    MEETING_TYPES = (
        ('ZOOM', 'اجتماع عبر زووم'),
        ('NORMAL', 'اجتماع عادي'),
        ('LIVE', 'اجتماع مباشر'),
    )
    
    NOTIFICATION_TYPES = (
        ('DAY_BEFORE', 'قبل يوم'),
        ('HOUR_BEFORE', 'قبل ساعة'),
        ('CANCELLED', 'تم الإلغاء'),
        ('RESCHEDULED', 'تم إعادة الجدولة'),
    )
    
    title = models.CharField(max_length=255, verbose_name="عنوان الاجتماع")
    description = models.TextField(verbose_name="وصف الاجتماع")
    meeting_type = models.CharField(max_length=10, choices=MEETING_TYPES, verbose_name="نوع الاجتماع")
    start_time = models.DateTimeField(verbose_name="وقت البدء")
    duration = models.DurationField(default=timedelta(minutes=60), verbose_name="المدة")
    # school field removed
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meetings', verbose_name="منشئ الاجتماع")
    zoom_link = models.URLField(blank=True, null=True, verbose_name="رابط زووم")
    recording_url = models.URLField(blank=True, null=True, verbose_name="رابط التسجيل")
    materials = models.FileField(upload_to='meeting_materials/', blank=True, null=True, verbose_name="مواد الاجتماع")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    # Fields for live meetings
    meeting_room_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="معرف غرفة الاجتماع")
    is_live_started = models.BooleanField(default=False, verbose_name="بدأ الاجتماع المباشر")
    live_started_at = models.DateTimeField(blank=True, null=True, verbose_name="وقت بدء الاجتماع المباشر")
    live_ended_at = models.DateTimeField(blank=True, null=True, verbose_name="وقت انتهاء الاجتماع المباشر")
    max_participants = models.IntegerField(default=50, verbose_name="الحد الأقصى للمشاركين")
    enable_screen_share = models.BooleanField(default=True, verbose_name="تمكين مشاركة الشاشة")
    enable_chat = models.BooleanField(default=True, verbose_name="تمكين الدردشة")
    enable_recording = models.BooleanField(default=False, verbose_name="تمكين التسجيل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    notification_task_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = "اجتماع"
        verbose_name_plural = "الاجتماعات"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"
    
    def clean(self):
        if self.meeting_type == 'ZOOM' and not self.zoom_link:
            raise ValidationError("يجب إضافة رابط زووم للاجتماعات عن بعد")
    
    @property
    def end_time(self):
        return self.start_time + self.duration
    
    @property
    def is_past(self):
        """Check if the meeting is in the past"""
        return timezone.now() > self.end_time
    
    @property
    def is_ongoing(self):
        """Check if the meeting is currently ongoing"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    @property
    def attendance_rate(self):
        """Calculate the attendance rate for this meeting"""
        total_participants = self.participant_set.count()
        if total_participants == 0:
            return 0
        attended = self.participant_set.filter(is_attending=True).count()
        return (attended / total_participants) * 100
    
    def get_participants(self):
        """Get all participants for this meeting"""
        return self.participant_set.all()
    
    def add_participant(self, user):
        """Add a participant to the meeting"""
        participant, created = Participant.objects.get_or_create(
            meeting=self,
            user=user
        )
        return participant
    
    def start_live_meeting(self):
        """Start the live meeting"""
        if self.meeting_type == 'LIVE' and not self.is_live_started:
            import uuid
            self.meeting_room_id = str(uuid.uuid4())
            self.is_live_started = True
            self.live_started_at = timezone.now()
            self.save()
            return True
        return False
    
    def end_live_meeting(self):
        """End the live meeting"""
        if self.meeting_type == 'LIVE' and self.is_live_started:
            self.live_ended_at = timezone.now()
            self.save()
            # Mark all participants as exited if they haven't already
            participants = self.participant_set.filter(exit_time__isnull=True, attendance_time__isnull=False)
            for participant in participants:
                participant.mark_exit()
            return True
        return False
    
    @property
    def can_join_live(self):
        """Check if user can join live meeting"""
        if self.meeting_type != 'LIVE':
            return False
        if not self.is_live_started:
            return False
        if self.live_ended_at:
            return False
        current_participants = self.participant_set.filter(
            attendance_time__isnull=False, 
            exit_time__isnull=True
        ).count()
        return current_participants < self.max_participants
    
    @property
    def live_participants_count(self):
        """Get current live participants count"""
        if self.meeting_type != 'LIVE':
            return 0
        return self.participant_set.filter(
            attendance_time__isnull=False, 
            exit_time__isnull=True
        ).count()

    def setup_notifications(self):
        """Set up automatic notifications for this meeting"""
        # Create day before notification
        day_before = self.start_time - timedelta(days=1)
        if day_before > timezone.now():
            Notification.objects.create(
                meeting=self,
                notification_type='DAY_BEFORE',
                scheduled_time=day_before,
                message=f"تذكير: لديك اجتماع {self.title} غداً في تمام {self.start_time.strftime('%H:%M')}"
            )
        
        # Create hour before notification
        hour_before = self.start_time - timedelta(hours=1)
        if hour_before > timezone.now():
            Notification.objects.create(
                meeting=self,
                notification_type='HOUR_BEFORE',
                scheduled_time=hour_before,
                message=f"تذكير: لديك اجتماع {self.title} بعد ساعة في تمام {self.start_time.strftime('%H:%M')}"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.setup_notifications()


class Participant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name="الاجتماع")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    is_attending = models.BooleanField(default=False, verbose_name="حاضر")
    attendance_time = models.DateTimeField(null=True, blank=True, verbose_name="وقت الحضور")
    exit_time = models.DateTimeField(null=True, blank=True, verbose_name="وقت المغادرة")
    attendance_duration = models.DurationField(null=True, blank=True, verbose_name="مدة الحضور")
    
    class Meta:
        unique_together = ('meeting', 'user')
        verbose_name = "مشارك"
        verbose_name_plural = "المشاركون"
    
    def __str__(self):
        return f"{self.user} - {self.meeting}"
    
    def mark_attendance(self):
        """Mark attendance for this participant"""
        if not self.is_attending:
            self.is_attending = True
            self.attendance_time = timezone.now()
            self.save()
    
    def mark_exit(self):
        """Mark exit time for this participant"""
        if self.is_attending and self.attendance_time and not self.exit_time:
            self.exit_time = timezone.now()
            self.attendance_duration = self.exit_time - self.attendance_time
            self.save()
    
    @property
    def attendance_status(self):
        """Get attendance status string"""
        if not self.is_attending:
            return "غائب"
        elif self.is_attending and not self.exit_time:
            return "حاضر"
        else:
            return "حضر وغادر"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('DAY_BEFORE', 'قبل يوم'),
        ('HOUR_BEFORE', 'قبل ساعة'),
        ('CANCELLED', 'تم الإلغاء'),
        ('RESCHEDULED', 'تم إعادة الجدولة'),
        ('CUSTOM', 'مخصص'),
    )
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name="الاجتماع")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='CUSTOM', verbose_name="نوع الإشعار")
    message = models.TextField(verbose_name="الرسالة")
    recipients = models.ManyToManyField(User, related_name='meeting_notifications', verbose_name="المستلمون")
    scheduled_time = models.DateTimeField(verbose_name="وقت الجدولة")
    sent = models.BooleanField(default=False, verbose_name="تم الإرسال")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="تمت القراءة")
    
    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"إشعار {self.get_notification_type_display()} - {self.meeting}"
    
    def send(self):
        """Send the notification to all recipients via email"""
        if not self.sent:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            
            # Get all recipient emails
            recipient_emails = [recipient.email for recipient in self.recipients.all() if recipient.email]
            
            if not recipient_emails:
                # No valid recipients, mark as sent but log this
                self.sent = True
                self.sent_at = timezone.now()
                self.save()
                return False
                
            # Prepare email context
            context = {
                'meeting': self.meeting,
                'message': self.message,
                'notification_type': self.get_notification_type_display(),
                'meeting_url': f"{settings.BASE_URL}/meetings/{self.meeting.id}/",
            }
            
            # Determine subject based on notification type
            subject_prefix = "إشعار اجتماع: "
            if self.notification_type == 'DAY_BEFORE':
                subject = f"{subject_prefix}تذكير قبل يوم - {self.meeting.title}"
            elif self.notification_type == 'HOUR_BEFORE':
                subject = f"{subject_prefix}تذكير قبل ساعة - {self.meeting.title}"
            elif self.notification_type == 'CANCELLED':
                subject = f"{subject_prefix}تم إلغاء الاجتماع - {self.meeting.title}"
            elif self.notification_type == 'RESCHEDULED':
                subject = f"{subject_prefix}تم إعادة جدولة الاجتماع - {self.meeting.title}"
            else:
                subject = f"{subject_prefix}{self.meeting.title}"
            
            # Render email template
            html_message = render_to_string('website/meetings/email/notification_email.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_emails,
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Mark as sent
                self.sent = True
                self.sent_at = timezone.now()
                self.save()
                return True
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error sending notification email: {e}")
                return False
        return False
    
    @classmethod
    def create_for_meeting(cls, meeting, notification_type, message, scheduled_time=None):
        """Create a notification for all participants of a meeting"""
        if scheduled_time is None:
            scheduled_time = timezone.now()
            
        notification = cls.objects.create(
            meeting=meeting,
            notification_type=notification_type,
            message=message,
            scheduled_time=scheduled_time
        )
        
        # Add all participants as recipients
        participants = meeting.participant_set.all()
        for participant in participants:
            notification.recipients.add(participant.user)
            
        # Add the creator as a recipient
        notification.recipients.add(meeting.creator)
        
        return notification
        
    @classmethod
    def get_unread_count(cls, user):
        """Get the count of unread notifications for a user"""
        return cls.objects.filter(recipients=user, is_read=False).count()


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('course', 'user')
        ordering = ['-created_at']
        verbose_name = 'Course Review (Legacy)'
        verbose_name_plural = 'Course Reviews (Legacy)'
    
    def __str__(self):
        return f"{self.user.username}'s review for {self.course.name}"
    
    def save(self, *args, **kwargs):
        # Call the original save method
        super().save(*args, **kwargs)
        # Update the course's average rating
        course = self.course
        reviews = Review.objects.filter(course=course)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            course.rating = round(avg_rating, 1)
            course.save(update_fields=['rating'])


class Book(models.Model):
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    book_file = models.FileField(upload_to='books/')
    cover_image = models.ImageField(upload_to='books/covers/', null=True, blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, related_name='books')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('published', 'منشور'),
    ]
    
    title = models.CharField(max_length=255, verbose_name='العنوان')
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط')
    content = RichTextField(verbose_name='المحتوى')
    summary = models.TextField(blank=True, null=True, verbose_name='ملخص')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='articles', verbose_name='الكاتب')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles', verbose_name='التصنيف')
    tags = models.ManyToManyField(Tags, blank=True, related_name='articles', verbose_name='الوسوم')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    image = models.ImageField(upload_to='articles/', null=True, blank=True, verbose_name='الصورة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    views_count = models.PositiveIntegerField(default=0, verbose_name='عدد المشاهدات')
    featured = models.BooleanField(default=False, verbose_name='مميز')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مقالة'
        verbose_name_plural = 'المقالات'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate a slug if it doesn't exist
        if not self.slug:
            from django.utils.text import slugify
            # Create a unique slug
            base_slug = slugify(self.title)
            unique_slug = base_slug
            num = 1
            while Article.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article_detail', kwargs={'slug': self.slug})
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    @property
    def reading_time(self):
        # Estimate reading time based on content length
        words_per_minute = 200  # Average reading speed
        word_count = len(self.content.split())
        minutes = word_count / words_per_minute
        return max(1, round(minutes))  # Minimum 1 minute


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        return sum(item.course.price for item in self.items.all())

    @property
    def total_items(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'course')

    def __str__(self):
        return f"{self.course.name} in {self.cart}"


class ContentProgress(models.Model):
    """Track user progress on different types of content"""
    CONTENT_TYPES = [
        ('note', 'Note/PDF'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)  # Store as string to handle different ID types
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course', 'content_type', 'content_id']
        verbose_name_plural = "Content Progress"
    
    def __str__(self):
        return f"{self.user.username} - {self.course.name} - {self.content_type} {self.content_id}"


class Comment(models.Model):
    """Comments on courses for discussion"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_comments', verbose_name='المستخدم')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='comments', verbose_name='الدورة')
    content = models.TextField(verbose_name='محتوى التعليق')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_comments', through='CommentLike')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تعليق'
        verbose_name_plural = 'التعليقات'
    
    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class SubComment(models.Model):
    """Replies to comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_replies', verbose_name='المستخدم')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies', verbose_name='التعليق الأصلي')
    content = models.TextField(verbose_name='محتوى الرد')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_subcomments', through='SubCommentLike')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'رد'
        verbose_name_plural = 'الردود'
    
    def __str__(self):
        return f"{self.user.username} - رد على: {self.comment}"


class CommentLike(models.Model):
    """Like system for comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'comment')
        verbose_name = 'إعجاب بالتعليق'
        verbose_name_plural = 'إعجابات التعليقات'
    
    def __str__(self):
        return f"{self.user.username} likes {self.comment}"


class SubCommentLike(models.Model):
    """Like system for sub-comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subcomment = models.ForeignKey(SubComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'subcomment')
        verbose_name = 'إعجاب بالرد'
        verbose_name_plural = 'إعجابات الردود'
    
    def __str__(self):
        return f"{self.user.username} likes {self.subcomment}"


# Signals for automatic progress tracking
@receiver(post_save, sender=Enrollment)
def create_user_progress_on_enrollment(sender, instance, created, **kwargs):
    """Create UserProgress when user enrolls in a course"""
    if created:
        try:
            UserProgress.objects.get_or_create(
                user=instance.student,
                course=instance.course
            )
        except Exception as e:
            print(f"Error creating UserProgress for enrollment: {e}")


# Signal to create course progress stats
@receiver(post_save, sender=Course)
def create_course_progress_stats(sender, instance, created, **kwargs):
    """Create CourseProgress stats when a course is created"""
    if created:
        try:
            CourseProgress.objects.get_or_create(course=instance)
        except Exception as e:
            print(f"Error creating CourseProgress stats: {e}")


# Signal to update progress when user completes quiz
@receiver(post_save, sender=QuizAttempt)
def update_progress_on_quiz_completion(sender, instance, created, **kwargs):
    """Update module progress when user completes a quiz"""
    if instance.end_time and instance.passed:  # Quiz is completed and passed
        try:
            if instance.quiz.module:
                progress = ModuleProgress.get_or_create_progress(
                    instance.user, 
                    instance.quiz.module
                )
                progress.mark_quiz_completed()
        except Exception as e:
            print(f"Error updating progress on quiz completion: {e}")


# Signal to update progress when user submits assignment
@receiver(post_save, sender=AssignmentSubmission)
def update_progress_on_assignment_submission(sender, instance, created, **kwargs):
    """Update module progress when user submits an assignment"""
    if created and instance.assignment.module:
        try:
            progress = ModuleProgress.get_or_create_progress(
                instance.user, 
                instance.assignment.module
            )
            # Mark as completed when assignment is submitted
            # You might want to change this logic based on grading
            progress.save()  # This will recalculate completion status
        except Exception as e:
            print(f"Error updating progress on assignment submission: {e}")


class MeetingChat(models.Model):
    """Chat messages for live meetings"""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='chat_messages', verbose_name="الاجتماع")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    message = models.TextField(verbose_name="الرسالة")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإرسال")
    is_system_message = models.BooleanField(default=False, verbose_name="رسالة نظام")
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "رسالة دردشة"
        verbose_name_plural = "رسائل الدردشة"
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


class CertificateTemplate(models.Model):
    """Certificate template settings for admins and teachers"""
    TEMPLATE_STYLE_CHOICES = [
        ('modern', 'تصميم حديث'),
        ('classic', 'تصميم كلاسيكي'),
        ('elegant', 'تصميم أنيق'),
        ('professional', 'تصميم مهني'),
        ('creative', 'تصميم إبداعي'),
        ('minimalist', 'تصميم بسيط'),
        ('colorful', 'تصميم ملون'),
        ('corporate', 'تصميم شركات'),
    ]
    
    COLOR_CHOICES = [
        ('#2a5a7c', 'أزرق'),
        ('#28a745', 'أخضر'),
        ('#dc3545', 'أحمر'),
        ('#ffc107', 'أصفر'),
        ('#6f42c1', 'بنفسجي'),
        ('#fd7e14', 'برتقالي'),
        ('#17a2b8', 'سماوي'),
        ('#e83e8c', 'وردي'),
        ('#6c757d', 'رمادي'),
        ('#343a40', 'أسود'),
    ]
    
    TEMPLATE_SOURCE_CHOICES = [
        ('custom', 'قالب مخصص'),
        ('preset', 'قالب جاهز'),
        ('imported', 'قالب مستورد'),
    ]
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="منشئ القالب")
    template_name = models.CharField(max_length=255, verbose_name="اسم القالب")
    template_style = models.CharField(max_length=20, choices=TEMPLATE_STYLE_CHOICES, default='modern', verbose_name="نمط الشهادة")
    template_source = models.CharField(max_length=20, choices=TEMPLATE_SOURCE_CHOICES, default='custom', verbose_name="مصدر القالب")
    primary_color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#2a5a7c', verbose_name="اللون الأساسي")
    secondary_color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#28a745', verbose_name="اللون الثانوي")
    institution_name = models.CharField(max_length=255, verbose_name="اسم المؤسسة")
    institution_logo = models.ImageField(upload_to='certificate_templates/logos/', null=True, blank=True, verbose_name="شعار المؤسسة")
    signature_name = models.CharField(max_length=255, verbose_name="اسم الموقع")
    signature_title = models.CharField(max_length=255, verbose_name="منصب الموقع")
    signature_image = models.ImageField(upload_to='certificate_templates/signatures/', null=True, blank=True, verbose_name="صورة التوقيع")
    
    # New field for user signature upload
    user_signature = models.ImageField(upload_to='certificate_templates/user_signatures/', null=True, blank=True, verbose_name="توقيع المستخدم")
    
    certificate_text = models.TextField(
        default="هذا يشهد بأن {student_name} قد أكمل بنجاح دورة {course_name} بتاريخ {completion_date}",
        verbose_name="نص الشهادة",
        help_text="يمكنك استخدام المتغيرات: {student_name}, {course_name}, {completion_date}, {institution_name}"
    )
    
    # Template styling options
    background_pattern = models.CharField(max_length=50, default='none', verbose_name="نمط الخلفية")
    border_style = models.CharField(max_length=50, default='classic', verbose_name="نمط الحدود")
    font_family = models.CharField(max_length=100, default='Arial', verbose_name="نوع الخط")
    
    include_qr_code = models.BooleanField(default=True, verbose_name="إضافة رمز QR للتحقق")
    include_grade = models.BooleanField(default=False, verbose_name="إضافة الدرجة في الشهادة")
    include_completion_date = models.BooleanField(default=True, verbose_name="إضافة تاريخ الإكمال")
    include_course_duration = models.BooleanField(default=False, verbose_name="إضافة مدة الدورة")
    
    # Template preview data
    preview_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات المعاينة")
    
    is_public = models.BooleanField(default=False, verbose_name="قالب عام (يمكن للجميع استخدامه)")
    is_default = models.BooleanField(default=False, verbose_name="القالب الافتراضي")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "قالب الشهادة"
        verbose_name_plural = "قوالب الشهادات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template_name} - {self.created_by.username}"
    
    def save(self, *args, **kwargs):
        # إذا تم تعيين هذا كافتراضي، يجب إزالة الافتراضي من الآخرين
        if self.is_default:
            CertificateTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_template(cls):
        """الحصول على القالب الافتراضي"""
        try:
            return cls.objects.filter(is_default=True, is_active=True).first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_public_templates(cls):
        """الحصول على القوالب العامة"""
        return cls.objects.filter(is_public=True, is_active=True)
    
    @classmethod
    def get_preset_templates(cls):
        """الحصول على القوالب الجاهزة"""
        return cls.objects.filter(template_source='preset', is_active=True)
    
    def format_certificate_text(self, student_name, course_name, completion_date, grade=None, course_duration=None):
        """تنسيق نص الشهادة مع البيانات الفعلية"""
        formatted_text = self.certificate_text.format(
            student_name=student_name,
            course_name=course_name,
            completion_date=completion_date,
            institution_name=self.institution_name
        )
        
        if self.include_grade and grade:
            formatted_text += f" بدرجة {grade}"
        
        if self.include_course_duration and course_duration:
            formatted_text += f" خلال {course_duration}"
            
        return formatted_text
    
    def get_template_css(self):
        """إرجاع CSS مخصص للقالب"""
        css_vars = {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'font_family': self.font_family,
            'background_pattern': self.background_pattern,
            'border_style': self.border_style,
        }
        return css_vars
    
    def duplicate_template(self, new_name, new_owner):
        """إنشاء نسخة من القالب"""
        new_template = CertificateTemplate.objects.create(
            created_by=new_owner,
            template_name=new_name,
            template_style=self.template_style,
            template_source='custom',
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            institution_name=self.institution_name,
            signature_name=self.signature_name,
            signature_title=self.signature_title,
            certificate_text=self.certificate_text,
            background_pattern=self.background_pattern,
            border_style=self.border_style,
            font_family=self.font_family,
            include_qr_code=self.include_qr_code,
            include_grade=self.include_grade,
            include_completion_date=self.include_completion_date,
            include_course_duration=self.include_course_duration,
            is_public=False,
            is_default=False,
            is_active=True,
        )
        
        # Copy images if they exist
        if self.institution_logo:
            new_template.institution_logo = self.institution_logo
        if self.signature_image:
            new_template.signature_image = self.signature_image
            
        new_template.save()
        return new_template


class PresetCertificateTemplate(models.Model):
    """Preset certificate templates that users can choose from"""
    name = models.CharField(max_length=255, verbose_name="اسم القالب الجاهز")
    description = models.TextField(verbose_name="وصف القالب")
    template_style = models.CharField(max_length=20, choices=CertificateTemplate.TEMPLATE_STYLE_CHOICES, verbose_name="نمط القالب")
    primary_color = models.CharField(max_length=7, default='#2a5a7c', verbose_name="اللون الأساسي")
    secondary_color = models.CharField(max_length=7, default='#28a745', verbose_name="اللون الثانوي")
    background_pattern = models.CharField(max_length=50, default='none', verbose_name="نمط الخلفية")
    border_style = models.CharField(max_length=50, default='classic', verbose_name="نمط الحدود")
    font_family = models.CharField(max_length=100, default='Arial', verbose_name="نوع الخط")
    preview_image = models.ImageField(upload_to='preset_templates/', verbose_name="صورة المعاينة")
    template_html = models.TextField(verbose_name="كود HTML للقالب")
    template_css = models.TextField(verbose_name="كود CSS للقالب")
    category = models.CharField(max_length=50, default='general', verbose_name="التصنيف")
    is_featured = models.BooleanField(default=False, verbose_name="قالب مميز")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "قالب جاهز"
        verbose_name_plural = "القوالب الجاهزة"
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.name
    
    def create_template_for_user(self, user, institution_name, signature_name, signature_title):
        """إنشاء قالب مخصص للمستخدم بناءً على القالب الجاهز"""
        template = CertificateTemplate.objects.create(
            created_by=user,
            template_name=f"{self.name} - {user.username}",
            template_style=self.template_style,
            template_source='preset',
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            background_pattern=self.background_pattern,
            border_style=self.border_style,
            font_family=self.font_family,
            institution_name=institution_name,
            signature_name=signature_name,
            signature_title=signature_title,
        )
        return template


class Certificate(models.Model):
    """Student course completion certificates"""
    STATUS_CHOICES = [
        ('active', 'نشطة'),
        ('revoked', 'ملغية'),
        ('expired', 'منتهية الصلاحية'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('verified', 'تم التحقق'),
        ('pending', 'في انتظار التحقق'),
        ('failed', 'فشل التحقق'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates', verbose_name="الطالب")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates', verbose_name="الدورة")
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="قالب الشهادة")
    
    certificate_id = models.CharField(max_length=100, unique=True, verbose_name="رقم الشهادة")
    date_issued = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإصدار")
    completion_date = models.DateTimeField(verbose_name="تاريخ إكمال الدورة")
    
    # Certificate content
    student_name = models.CharField(max_length=255, verbose_name="اسم الطالب")
    course_title = models.CharField(max_length=500, verbose_name="عنوان الدورة")
    institution_name = models.CharField(max_length=255, default="أكاديمية التعلم الإلكتروني", verbose_name="اسم المؤسسة")
    
    # Performance data
    final_grade = models.FloatField(null=True, blank=True, verbose_name="الدرجة النهائية")
    completion_percentage = models.FloatField(default=100.0, verbose_name="نسبة الإكمال")
    course_duration_hours = models.IntegerField(null=True, blank=True, verbose_name="مدة الدورة بالساعات")
    
    # Certificate status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="حالة الشهادة")
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='verified', verbose_name="حالة التحقق")
    verification_code = models.CharField(max_length=50, unique=True, verbose_name="رمز التحقق")
    
    # Metadata
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_certificates', verbose_name="أصدرت بواسطة")
    pdf_file = models.FileField(upload_to='certificates/pdfs/', null=True, blank=True, verbose_name="ملف PDF")
    qr_code_image = models.ImageField(upload_to='certificates/qr_codes/', null=True, blank=True, verbose_name="صورة رمز QR")
    
    # Digital signature
    digital_signature = models.TextField(null=True, blank=True, verbose_name="التوقيع الرقمي")
    signature_verified = models.BooleanField(default=False, verbose_name="تم التحقق من التوقيع")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "شهادة"
        verbose_name_plural = "الشهادات"
        unique_together = ('user', 'course')
        ordering = ['-date_issued']
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"شهادة {self.student_name} - {self.course_title}"
    
    def save(self, *args, **kwargs):
        # Generate certificate ID if not exists
        if not self.certificate_id:
            import time
            timestamp = int(time.time())
            self.certificate_id = f"CERT-{self.course.id:04d}-{self.user.id:04d}-{timestamp}"
        
        # Generate verification code if not exists
        if not self.verification_code:
            import secrets
            import string
            alphabet = string.ascii_uppercase + string.digits
            self.verification_code = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Set student name and course title
        if not self.student_name:
            profile = getattr(self.user, 'profile', None)
            self.student_name = profile.name if profile and profile.name else self.user.get_full_name() or self.user.username
        
        if not self.course_title:
            self.course_title = self.course.name
        
        # Set completion date if not exists
        if not self.completion_date:
            self.completion_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_verification_url(self):
        """إرجاع رابط التحقق من الشهادة"""
        from django.urls import reverse
        return reverse('verify_certificate', kwargs={'verification_code': self.verification_code})
    
    def get_download_url(self):
        """إرجاع رابط تحميل الشهادة"""
        from django.urls import reverse
        return reverse('download_certificate', kwargs={'certificate_id': self.id})
    
    def get_template_or_default(self):
        """الحصول على القالب المستخدم أو القالب الافتراضي"""
        if self.template and self.template.is_active:
            return self.template
        return CertificateTemplate.get_default_template()
    
    def generate_qr_code(self):
        """إنتاج رمز QR للتحقق من الشهادة"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile
            from django.conf import settings
            
            # Create QR code with verification URL
            verification_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}{self.get_verification_url()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save to file
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            filename = f"qr_{self.certificate_id}.png"
            self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)
            
            return True
        except ImportError:
            print("qrcode library not installed. Install with: pip install qrcode[pil]")
            return False
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return False
    
    def is_valid(self):
        """التحقق من صلاحية الشهادة"""
        return self.status == 'active' and self.verification_status == 'verified'
    
    def revoke(self, reason=""):
        """إلغاء الشهادة"""
        self.status = 'revoked'
        self.save()
    
    def get_grade_display(self):
        """عرض الدرجة بصورة مناسبة"""
        if self.final_grade:
            return f"{self.final_grade:.1f}%"
        return "ممتاز"
    
    def get_duration_display(self):
        """عرض مدة الدورة بصورة مناسبة"""
        if self.course_duration_hours:
            return f"{self.course_duration_hours} ساعة"
        return getattr(self.course, 'vidoes_time', 'غير محدد')


class UserSignature(models.Model):
    """User digital signatures for certificates"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signatures', verbose_name="المستخدم")
    signature_name = models.CharField(max_length=255, verbose_name="اسم التوقيع")
    signature_image = models.ImageField(upload_to='user_signatures/', verbose_name="صورة التوقيع")
    signature_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="المنصب")
    is_default = models.BooleanField(default=False, verbose_name="التوقيع الافتراضي")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        verbose_name = "توقيع المستخدم"
        verbose_name_plural = "توقيعات المستخدمين"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.signature_name} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # إذا تم تعيين هذا كافتراضي، يجب إزالة الافتراضي من الآخرين للمستخدم نفسه
        if self.is_default:
            UserSignature.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)



