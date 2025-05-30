from django.urls import path
from . import views_debug

# Debug URLs
urlpatterns = [
    path('debug-teacher-courses/', views_debug.debug_teacher_courses, name='debug_teacher_courses'),
]
