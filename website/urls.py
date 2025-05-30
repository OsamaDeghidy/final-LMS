from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.index,name='index'),
    path('contact/',views.contact,name='contact'),
    path('create_course',views.create_course,name='create_course'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/update/', views.update_course, name='update_course'),
    path('course/delete/', views.delete_course, name='delete_course'),
    path('course/', views.course, name='course'),
    path('allcourses/', views.allcourses, name='allcourses'),
    path('create_module/<int:course_id>/', views.create_module, name='create_module'),
    path('course/<int:course_id>/module/<int:module_id>/update/', views.update_module, name='update_module'),
    path('course/<int:course_id>/module/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    path('<int:course_id>/modules/', views.course_modules, name='course_modules'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz_list/<int:video_id>/', views.quiz_list, name='quiz_list'),
    path('quiz/create/<int:video_id>/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>', views.view_quiz, name='quiz_detail'),
    path('quiz/<int:pk>/update/', views.update_quiz, name='update_quiz'),
    path('user_teacher/', views.make_teacher, name='make_teacher'),
    path('teacher_list/', views.teacher_list, name='teacher_list'),

    path('courseviewpage/<int:course_id>/', views.courseviewpage, name='courseviewpage'),
    path('courseviewpage/<int:course_id>/video/<int:video_id>/', views.courseviewpagevideo, name='courseviewpagevideo'),
    path('courseviewpage/<int:course_id>/note/<int:note_id>/', views.courseviewpagenote, name='courseviewpagenote'),
    path('api/video/<int:video_id>/mark-watched/', views.mark_video_watched, name='mark_video_watched'),


    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('analytics/', views.analytics, name='analytic'),
    path('submit_quiz/', views.submit_quiz, name='submit_quiz'),
    path('delete-pdf/<int:course_id>/<str:pdf_type>/', views.delete_pdf, name='delete_pdf'),
    path('course-category/<str:category_slug>/', views.course_category, name='course_category'),
    path('course/<int:course_id>/add-comment/', views.add_comment, name='add_comment'),
    #path('create_course', views.create_course, name='create_course'),  # Add this line
    
    # Cart URLs
    path('cart/add/<int:course_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:course_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

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
