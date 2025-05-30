from django.urls import path
from . import views_enrollment

# Enrollment URLs
urlpatterns = [
    path('my-courses/', views_enrollment.my_courses, name='my_courses'),
    path('teacher-courses/', views_enrollment.teacher_courses, name='teacher_courses'),
]
