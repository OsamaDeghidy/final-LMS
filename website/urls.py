from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext as _
from . import views, views_course
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    
    # Include all course-related URLs
    path('', include('website.urls_course')),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Teacher list
    path('teacher_list/', views.teacher_list, name='teacher_list'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytic'),
    
    # Quiz submission
    path('submit-quiz/', views.submit_quiz, name='submit_quiz'),
    
    # File management
    path('delete-pdf/<int:course_id>/<str:pdf_type>/', views.delete_pdf, name='delete_pdf'),
    path('delete-module-pdf/<int:module_id>/<str:pdf_type>/', views.delete_module_pdf, name='delete_module_pdf'),
    
    # Course enrollment
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    
    # Comments and categories
    path('course/<int:course_id>/add-comment/', views.add_comment, name='add_comment'),
    path('course-category/<str:category_slug>/', views.course_category, name='course_category'),
    # Debug URLs
    path('debug/', include('website.urls_debug')),
    path('quiz_list/<int:video_id>/', views.quiz_list, name='quiz_list'),
    path('quiz/create/<int:video_id>/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>', views.view_quiz, name='quiz_detail'),
    path('quiz/<int:pk>/update/', views.update_quiz, name='update_quiz'),
    path('teacher_list/', views.teacher_list, name='teacher_list'),

    path('courseviewpage/<int:course_id>/', views.courseviewpage, name='courseviewpage'),
    path('courseviewpage/<int:course_id>/video/<int:video_id>/', views.courseviewpagevideo, name='courseviewpagevideo'),
    path('courseviewpage/<int:course_id>/note/<int:note_id>/', views.courseviewpagenote, name='courseviewpagenote'),
    path('api/video/<int:video_id>/mark-watched/', views.mark_video_watched, name='mark_video_watched'),
    path('api/<str:content_type>/<int:content_id>/mark-viewed/', views.mark_content_viewed, name='mark_content_viewed'),
    path('api/<str:content_type>/<int:content_id>/mark-completed/', views.mark_content_viewed, name='mark_content_completed'),
    path('api/assignment/<int:assignment_id>/mark-completed/', views.mark_assignment_completed, name='mark_assignment_completed'),

    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('analytics/', views.analytics, name='analytic'),
    path('submit-quiz/', views.submit_quiz, name='submit_quiz'),
    path('delete-pdf/<int:course_id>/<str:pdf_type>/', views.delete_pdf, name='delete_pdf'),
    path('delete-module-pdf/<int:module_id>/<str:pdf_type>/', views.delete_module_pdf, name='delete_module_pdf'),
    path('course-category/<str:category_slug>/', views.course_category, name='course_category'),
    path('course/<int:course_id>/add-comment/', views.add_comment, name='add_comment'),
    #path('create_course', views.create_course, name='create_course'),  # Add this line
    
    # Cart URLs
    path('cart/add/<int:course_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:course_id>/', views.remove_from_cart, name='remove_from_cart'),
    # Checkout and API endpoints are now in urls_course.py
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Include course URLs
from . import urls_course

urlpatterns += urls_course.urlpatterns

# Include assignment URLs directly
from . import views_assignment

# Assignment URLs
urlpatterns += [
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

# Include article URLs
from . import urls_article

urlpatterns += urls_article.urlpatterns

# Include enrollment URLs
from . import urls_enrollment

urlpatterns += urls_enrollment.urlpatterns

# Include exam URLs
from . import urls_exam

urlpatterns += urls_exam.urlpatterns

# Include attendance URLs
from . import attendance_urls

urlpatterns += [
    path('attendance/', include('website.attendance_urls')),
]

# Include meeting URLs
from . import meeting_urls

urlpatterns += meeting_urls.urlpatterns

# Course URLs are included in the main URL patterns above
