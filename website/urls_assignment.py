from django.urls import path
from . import views_assignment

urlpatterns = [
    path('assignments/', views_assignment.all_assignments, name='all_assignments'),
    path('course/<int:course_id>/assignments/', views_assignment.assignment_list, name='assignment_list'),
    path('course/<int:course_id>/assignments/create/', views_assignment.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/', views_assignment.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_id>/update/', views_assignment.update_assignment, name='update_assignment'),
    path('assignment/<int:assignment_id>/delete/', views_assignment.delete_assignment, name='delete_assignment'),
    path('assignment/<int:assignment_id>/submit/', views_assignment.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/grade/', views_assignment.grade_submission, name='grade_submission'),
    path('delete-attachment/<int:attachment_id>/', views_assignment.delete_attachment, name='delete_attachment'),
]
