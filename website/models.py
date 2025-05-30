from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import uuid
from django.utils import timezone
from user.models import Profile,Organization,Teacher,Student
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
        is_new = not self.pk  # Check if this is a new course
        if is_new:  # If this is a new course (not yet saved)
            # For new courses, just save without calculating videos
            super().save(*args, **kwargs)
            return  # Exit early for new courses
        
        # For existing courses, update video counts and time
        self.total_video = Video.objects.filter(course=self).count()
        time = sum([video.duration for video in Video.objects.filter(course=self)])
        self.vidoes_time = str(timedelta(seconds=time))
        
        # Save with the updated values
        super().save(*args, **kwargs)
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

    def __str__(self):
        return f"{self.course.name} - {self.student.username}"



class Module(models.Model):
    name = models.CharField(max_length=2000, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    number = models.IntegerField(null=True, blank=True)    
    description = RichTextField(null=True, blank=True)
    total_video = models.IntegerField(null=True, blank=True, default=0)
    total_notes = models.IntegerField(null=True, blank=True, default=0)
    duration = models.CharField(max_length=2000, blank=True, null=True)

    def get_ordered_content(self):
        """
        Returns a list of all content (videos and quizzes) in the module in the correct order.
        Each item is a dictionary with a 'type' field ('video' or 'quiz') and the object.
        """
        content = []
        
        # Add videos
        for video in self.video_set.all().order_by('number'):
            content.append({
                'type': 'video',
                'id': video.id,
                'name': video.name,
                'duration': video.duration,
                'object': video
            })
            
            # Add quizzes for this video
            for quiz in video.quiz_set.all():
                content.append({
                    'type': 'quiz',
                    'id': quiz.id,
                    'title': quiz.title,
                    'video': video,
                    'questions_count': quiz.questions.count(),
                    'object': quiz
                })
        
        # Add module-level quizzes
        for quiz in self.module_quizzes.all():
            content.append({
                'type': 'quiz',
                'id': quiz.id,
                'title': quiz.title,
                'video': None,
                'questions_count': quiz.questions.count(),
                'object': quiz
            })
            
        return content

    def save(self, *args, **kwargs):
        # Save the instance first to ensure it has a primary key
        if not self.pk:
            super().save(*args, **kwargs)
        
        # Perform related queries and update fields
        self.total_video = Video.objects.filter(module=self).count()
        time = sum([video.duration for video in Video.objects.filter(module=self)])
        self.duration = str(timedelta(seconds=time))
        
        # Save again to persist the updated fields
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name + " - " + self.course.name



class Video(models.Model):
    name = models.CharField(max_length=2000, null=True, blank=True)
    number=models.IntegerField(blank=True,null=True, default=0)
    course=models.ForeignKey(Course,on_delete=models.SET_NULL,blank=True,null=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, blank=True, null=True)
    video = models.FileField(null=True, blank=True)
    duration = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # First save the course if it's a new instance
        is_new = not self.pk  # Check if this is a new course
        super().save(*args, **kwargs)
        if is_new:
            # Update the course's video count
            if self.course:
                videos = Video.objects.filter(course=self.course).count()
                self.course.total_video = videos
                self.course.save()

    def __str__(self):
        return self.name + " - " + self.module.name + " - " + self.course.name



class VideoProgress(models.Model):
    """Tracks a student's progress through a video"""
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)  # Whether the video has been watched
    watch_time = models.IntegerField(default=0)  # Seconds watched
    last_position = models.IntegerField(default=0)  # Last position in the video in seconds
    completed_at = models.DateTimeField(null=True, blank=True)  # When the video was completed
    last_watched = models.DateTimeField(auto_now=True)  # When the video was last watched
    
    class Meta:
        unique_together = ('student', 'video')
        
    def __str__(self):
        return f"{self.student.username} - {self.video.name} - {'Completed' if self.watched else 'In Progress'}"
        
    def mark_as_watched(self):
        """Mark the video as watched"""
        if not self.watched:
            self.watched = True
            self.completed_at = timezone.now()
            self.save(update_fields=['watched', 'completed_at'])
            
            # Update enrollment progress
            enrollment = Enrollment.objects.filter(
                student=self.student, 
                course=self.video.course
            ).first()
            
            if enrollment:
                # Calculate progress
                total_videos = Video.objects.filter(module__course=self.video.course).count()
                completed_videos = VideoProgress.objects.filter(
                    student=self.student,
                    video__module__course=self.video.course,
                    watched=True
                ).count()
                
                if total_videos > 0:
                    progress = (completed_videos / total_videos) * 100
                    enrollment.progress = progress
                    enrollment.save(update_fields=['progress'])
                    
                    # Check if course is completed
                    if progress >= 100:
                        enrollment.status = 'completed'
                        enrollment.save(update_fields=['status'])



class Comment(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    description=RichTextField(null=True, blank=True)
    video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        if self.video and self.course:
            raise ValueError("Comment can only be linked to a video or a Course, not both.")
        super().save(*args, **kwargs)

    def __str__(self):
        video_name = self.video.name if self.video else "No Video"
        course_name = self.course.name if self.course else "No Course"
        #desc = self.description if self.description else ""
        user_name = self.user.profile.name
        return f"{user_name} - {video_name} - {course_name}"



class SubComment(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    comment=models.ForeignKey(Comment, on_delete=models.CASCADE,null=True,blank=True)
    description=RichTextField(null=True, blank=True)
    def __str__(self):
        video_name = self.comment.video.name if self.comment.video else "No Video"
        course_name = self.comment.course.name if self.comment.course else "No Course"
        #desc = self.description if self.description else ""
        user_name = self.user.profile.name
        return f"{user_name} - {video_name} - {course_name}"




class Notes(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    description=RichTextField(null=True, blank=True) 
    number=models.IntegerField(blank=True,null=True, default=0) 
    video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        foreign_key_count = sum([bool(getattr(self, f)) for f in ['video', 'module', 'course']])
        if foreign_key_count > 1:
            raise ValueError("Comment can only be linked to one of video, module, or Course.")
        super().save(*args, **kwargs) 

    def __str__(self):
        video_name = self.video.name if self.video else "No Video"
        module_name = self.module.name if self.module else "No Module"
        course_name = self.course.name if self.course else "No Course"
        #desc = self.description if self.description else ""
        user_name = self.user.profile.name
        return f"{user_name} - {video_name} - {module_name} - {course_name}"





class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    number_of_videos_watched = models.IntegerField(default=0)
    total_number_of_videos = models.IntegerField(default=0)
    last_video_watched = models.ForeignKey(
        Video,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="last video watched",
    )
    progress_percent = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if self.total_number_of_videos == 0:
            self.progress_percent = 0
        else:
            self.progress_percent = (
                self.number_of_videos_watched / self.total_number_of_videos
            ) * 100
        super().save(*args, **kwargs)   

    def __str__(self):
        user_name = self.user.profile.name if self.user else "No User"


class CourseProgress(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    total_number_of_videos = models.IntegerField(default=0)
    # ... (rest of the code remains the same)
    total_number_of_users = models.IntegerField(default=0)
    total_progress_percent = models.FloatField(default=0)

    def calculate_progress_percent(self):
        if self.total_number_of_users == 0:
            self.total_progress_percent = 0
        else:
            self.total_progress_percent = (self.number_of_videos_watched / (self.total_number_of_videos * self.total_number_of_users)) * 100

    def save(self, *args, **kwargs):
        self.total_number_of_users = self.course.enroller_user.count()
        self.total_number_of_videos = self.course.video_set.count()
        self.number_of_videos_watched = sum([userprogress.number_of_videos_watched for userprogress in UserProgress.objects.filter(course=self.course)])
        self.calculate_progress_percent()
        super().save(*args, **kwargs)

    def __str__(self):
        course_name = self.course.name if self.course else "No Course"
        return f"{course_name} - {self.total_progress_percent} - {self.total_number_of_users} - {self.total_number_of_videos}"






class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ('video', 'فيديو كويز'),
        ('module', 'كويز وحدة'),
        ('quick', 'كويز سريع'),
    ]
    
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
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


class Monitor(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE,null=True,blank=True)
    ip=models.CharField(max_length=2000,blank=True,null=True)
    country=models.CharField(max_length=2000,blank=True,null=True)
    city=models.CharField(max_length=2000,blank=True,null=True)
    region=models.CharField(max_length=2000,blank=True,null=True)
    timeZone=models.CharField(max_length=2000,blank=True,null=True)
    browser=models.CharField(max_length=2000,blank=True,null=True)
    browser_version=models.CharField(max_length=2000,blank=True,null=True)
    operating_system=models.CharField(max_length=2000,blank=True,null=True)
    device=models.CharField(max_length=2000,blank=True,null=True)
    language=models.CharField(max_length=2000,blank=True,null=True)
    screen_resolution=models.CharField(max_length=2000,blank=True,null=True)
    referrer=models.CharField(max_length=2000,blank=True,null=True)
    landing_page=models.CharField(max_length=2000,blank=True,null=True)
    timestamp=models.DateTimeField(default=timezone.now)
    frequency=models.IntegerField(default=0,null=True,blank=True)

    def __str__(self):
        user_name = self.user.profile.name if self.user else "No User"
        return f"{user_name} - {self.ip} - {self.landing_page}"

    # class Meta:
    #     unique_together = ('user', 'ip', 'landing_page')


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
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField(default=timezone.now)
    time_out = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_present = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'course', 'date', 'video']
    
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


class School(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    def __str__(self):
        return self.name


class Meeting(models.Model):
    MEETING_TYPES = (
        ('ZOOM', 'اجتماع عبر زووم'),
        ('NORMAL', 'اجتماع عادي'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    meeting_type = models.CharField(max_length=10, choices=MEETING_TYPES)
    start_time = models.DateTimeField()
    duration = models.DurationField(default=timedelta(minutes=60))
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    zoom_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notification_task_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"
    
    def clean(self):
        if self.meeting_type == 'ZOOM' and not self.zoom_link:
            raise ValidationError("يجب إضافة رابط زووم للاجتماعات عن بعد")
    
    @property
    def end_time(self):
        return self.start_time + self.duration
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Note: setup_notifications method would need to be implemented
        # self.setup_notifications()


class Participant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_attending = models.BooleanField(default=False)
    attendance_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('meeting', 'user')
    
    def __str__(self):
        return f"{self.user} - {self.meeting}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"إشعار لـ {self.user} - {self.meeting}"


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('course', 'user')
        ordering = ['-created_at']
    
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


class ArticleCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='articles/', null=True, blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


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

