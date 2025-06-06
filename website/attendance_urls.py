from django.urls import path
from . import attendance_views

urlpatterns = [
    # Dashboard and main views
    path('dashboard/', attendance_views.attendance_dashboard, name='attendance_dashboard'),
    path('course/<int:course_id>/', attendance_views.course_attendance, name='course_attendance'),
    path('report/<int:course_id>/', attendance_views.attendance_report, name='attendance_report'),
    
    # API endpoints for marking attendance
    path('mark/', attendance_views.mark_attendance, name='mark_attendance'),
    path('mark-out/', attendance_views.mark_attendance_out, name='mark_attendance_out'),
    
    # Student details (for AJAX loading)
    path('student-details/<int:course_id>/<int:student_id>/', 
         attendance_views.student_details, name='student_details'),
    
    # Print reports
    path('print-report/<int:course_id>/', 
         attendance_views.print_attendance_report, name='print_attendance_report'),
    
    # Live session attendance
    path('create-live-session/', 
         attendance_views.create_live_session, name='create_live_session'),
         
    # Video attendance tracking
    path('auto-track/<int:video_id>/', 
         attendance_views.auto_attendance_tracking, name='auto_attendance_tracking'),
]
