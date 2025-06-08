from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course listing and details
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/content/', views.course_content, name='course_content'),
    
    # PDF views
    path('<int:course_id>/module/<int:module_id>/pdf/', views.module_pdf_view, name='module_pdf_view'),
    path('<int:course_id>/materials/', views.course_materials_view, name='course_materials_view'),
    path('<int:course_id>/syllabus/', views.course_syllabus_view, name='course_syllabus_view'),
    
    # Assignments and exams
    path('<int:course_id>/assignments/', views.course_assignments, name='course_assignments'),
    path('<int:course_id>/exams/', views.course_exams, name='course_exams'),
    
    # API endpoints
    path('mark-viewed/<str:content_type>/<int:content_id>/', views.mark_content_viewed, name='mark_content_viewed'),
    path('mark-pdf-read/', views.mark_pdf_read, name='mark_pdf_read'),
    path('<int:course_id>/recalculate-progress/', views.recalculate_progress, name='recalculate_progress'),
]
