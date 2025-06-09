from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ckeditor.fields import RichTextField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import os
class Profile(models.Model):
    name = models.CharField(max_length=2000, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.CharField(max_length=2000, blank=True, null=True)
    phone = models.CharField(max_length=2000, blank=True, null=True)
    status_choices = (
        ('Admin', 'Admin'),
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Organization', 'Organization')
    )
    status = models.CharField(max_length=2000, choices=status_choices, blank=True, null=True, default='Student')
    image_profile = models.ImageField(null=True, blank=True, default='blank.png', upload_to='user_profile/')
    shortBio = models.CharField(max_length=2000, blank=True, null=True)
    detail = RichTextField(null=True, blank=True)
    github = models.URLField(null=True, blank=True)
    youtube = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)

    def is_admin(self):
        return self.status == 'Admin' or self.user.is_superuser


class Organization(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    description = RichTextField(blank=True, null=True)
    location = models.CharField(max_length=2000, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    founded_year = models.DateField(blank=True, null=True)
    employees = models.IntegerField(blank=True, null=True, default = 0)


class Teacher(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=2000, blank=True, null=True)
    qualification = models.CharField(max_length=2000, blank=True, null=True)
    bio = RichTextField(blank=True, null=True)    
    date_of_birth = models.DateField(blank=True, null=True)
    research_interests = RichTextField(blank=True, null=True)
    def __str__(self):
        return self.profile.name

class Student(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=2000, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    def __str__(self):
        return self.profile.name


class TeacherApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    ]
    
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='teacher_applications')
    bio = models.TextField(verbose_name='نبذة عنك')
    specialization = models.CharField(max_length=255, verbose_name='التخصص')
    cv = models.FileField(upload_to='teacher_applications/cvs/', null=True, blank=True, verbose_name='السيرة الذاتية')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='حالة الطلب')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ المراجعة')
    notes = models.TextField(null=True, blank=True, verbose_name='ملاحظات')
    
    class Meta:
        verbose_name = 'طلب انضمام معلم'
        verbose_name_plural = 'طلبات الانضمام كمعلمين'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'طلب انضمام {self.profile.user.username} - {self.get_status_display()}'
    
    def approve(self):
        if self.status == 'pending':
            from django.db import connection, transaction
            import logging
            
            logger = logging.getLogger(__name__)
            
            try:
                with transaction.atomic():
                    logger.info(f"Starting approval for teacher application ID: {self.id}")
                    
                    # 1. Get the profile and log current status
                    profile = self.profile
                    logger.info(f"Current profile status before update: {profile.status}")
                    
                    # 2. Update profile status directly using raw SQL to bypass any model save methods
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE user_profile SET status = %s WHERE id = %s",
                            ['Teacher', str(profile.id)]
                        )
                        logger.info(f"Executed direct SQL to update profile {profile.id} status to Teacher")
                    
                    # 3. Refresh the profile from database
                    profile.refresh_from_db(fields=['status'])
                    logger.info(f"Profile status after direct SQL update: {profile.status}")
                    
                    # 4. Delete student profile if it exists
                    try:
                        student_count, _ = Student.objects.filter(profile=profile).delete()
                        if student_count > 0:
                            logger.info(f"Deleted student profile for user {profile.user.username}")
                        else:
                            logger.info("No student profile found to delete")
                    except Exception as e:
                        logger.error(f"Error deleting student profile: {str(e)}", exc_info=True)
                        raise
                    
                    # 5. Create or update Teacher profile
                    teacher, created = Teacher.objects.get_or_create(
                        profile=profile,
                        defaults={
                            'bio': self.bio,
                            'qualification': self.specialization
                        }
                    )
                    
                    if not created:
                        teacher.bio = self.bio
                        teacher.qualification = self.specialization
                        teacher.save(update_fields=['bio', 'qualification'])
                    
                    logger.info(f"{'Created' if created else 'Updated'} teacher profile with ID: {teacher.id}")
                    
                    # 6. Update the application status
                    self.status = 'approved'
                    self.reviewed_at = timezone.now()
                    self.save(update_fields=['status', 'reviewed_at'])
                    
                    # 7. Final verification
                    profile.refresh_from_db(fields=['status'])
                    if profile.status != 'Teacher':
                        raise ValueError(f"Profile status still not updated after all operations. Status: {profile.status}")
                    
                    logger.info(f"Successfully approved teacher application {self.id}")
                    return True
                    
            except Exception as e:
                logger.error(f"Critical error in approve(): {str(e)}", exc_info=True)
                return False
                
        return False
    
    def reject(self, notes=None):
        if self.status == 'pending':
            try:
                logger = logging.getLogger(__name__)
                logger.info(f"Rejecting teacher application ID: {self.id}")
                
                # Update application status
                self.status = 'rejected'
                self.reviewed_at = timezone.now()
                if notes:
                    self.notes = notes
                self.save(update_fields=['status', 'reviewed_at', 'notes'] if notes else ['status', 'reviewed_at'])
                
                logger.info(f"Application {self.id} rejected successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error rejecting application {self.id}: {str(e)}", exc_info=True)
                return False
        return False


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create or update user profile when a User is saved.
    Automatically creates an admin profile for superusers.
    """
    if created:
        if instance.is_superuser:
            Profile.objects.create(
                user=instance,
                name=instance.get_full_name() or instance.username,
                email=instance.email,
                status='Admin'
            )
        else:
            # Create a regular profile for non-superusers
            Profile.objects.create(
                user=instance,
                name=instance.get_full_name() or instance.username,
                email=instance.email
            )
    else:
        # Update the profile if user is updated to superuser
        if instance.is_superuser:
            if hasattr(instance, 'profile'):
                instance.profile.status = 'Admin'
                instance.profile.save(update_fields=['status'])
            else:
                Profile.objects.create(
                    user=instance,
                    name=instance.get_full_name() or instance.username,
                    email=instance.email,
                    status='Admin'
                )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to update profile when user details change
    """
    if hasattr(instance, 'profile'):
        instance.profile.email = instance.email
        instance.profile.name = instance.get_full_name() or instance.username
        instance.profile.save(update_fields=['email', 'name'])
    elif instance.is_superuser:
        # If this is a superuser without a profile, create one
        Profile.objects.create(
            user=instance,
            name=instance.get_full_name() or instance.username,
            email=instance.email,
            status='Admin'
        )