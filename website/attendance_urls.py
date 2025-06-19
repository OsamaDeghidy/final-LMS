from django.urls import path
from . import attendance_views

urlpatterns = [
    # Student Progress Dashboard and main views
    path('dashboard/', attendance_views.attendance_dashboard, name='attendance_dashboard'),
    path('course/<int:course_id>/', attendance_views.course_attendance, name='course_attendance'),
    
    # Alternative URL names for compatibility
    path('progress/', attendance_views.attendance_dashboard, name='progress_dashboard'),
    path('course-progress/<int:course_id>/', attendance_views.course_attendance, name='course_progress'),
]
