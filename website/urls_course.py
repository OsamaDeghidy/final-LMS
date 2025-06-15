from django.urls import path
from . import views_course

urlpatterns = [
    # Course browsing and details
    path('create_course/', views_course.create_course, name='create_course'),
    path('course/<int:course_id>/', views_course.course_detail, name='course_detail'),
    path('<int:course_id>/update/', views_course.update_course, name='update_course'),
    path('course/delete/', views_course.delete_course, name='delete_course'),
    path('course/', views_course.course, name='course'),
    path('allcourses/', views_course.allcourses, name='allcourses'),
    path('course-category/<str:category_slug>/', views_course.course_category, name='course_category'),
    path('course/<int:course_id>/add-comment/', views_course.add_comment, name='add_comment'),
    
    # Course modules management
    path('create_module/<int:course_id>/', views_course.create_module, name='create_module'),
    path('course/<int:course_id>/module/<int:module_id>/update/', views_course.update_module, name='update_module'),
    path('course/<int:course_id>/module/<int:module_id>/delete/', views_course.delete_module, name='delete_module'),
    path('<int:course_id>/modules/', views_course.course_modules, name='course_modules'),
    
    # Course viewing and content
    path('courseviewpage/<int:course_id>/', views_course.courseviewpage, name='courseviewpage'),
    path('courseviewpage/<int:course_id>/video/<int:video_id>/', views_course.courseviewpagevideo, name='courseviewpagevideo'),
    path('courseviewpage/<int:course_id>/note/<int:note_id>/', views_course.courseviewpagenote, name='courseviewpagenote'),
    
    # Quiz management
    path('quiz_list/<int:video_id>/', views_course.quiz_list, name='quiz_list'),
    path('quiz/create/<int:video_id>/', views_course.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>', views_course.view_quiz, name='quiz_detail'),
    path('quiz/<int:pk>/update/', views_course.update_quiz, name='update_quiz'),
    path('submit-quiz/', views_course.submit_quiz, name='submit_quiz'),
    
    # Course enrollment
    path('enroll/<int:course_id>/', views_course.enroll_course, name='enroll_course'),
    
    # API endpoints for progress tracking
    path('api/video/<int:video_id>/mark-watched/', views_course.mark_video_watched, name='mark_video_watched'),
    path('api/<str:content_type>/<int:content_id>/mark-viewed/', views_course.mark_content_viewed, name='mark_content_viewed'),
    path('api/<str:content_type>/<int:content_id>/mark-completed/', views_course.mark_content_viewed, name='mark_content_completed'),
    path('api/assignment/<int:assignment_id>/mark-completed/', views_course.mark_assignment_completed, name='mark_assignment_completed'),
    path('api/course/<int:course_id>/complete/', views_course.complete_course, name='complete_course'),
    path('api/course/<int:course_id>/recalculate-progress/', views_course.recalculate_progress, name='recalculate_progress'),
    
    # Course file management
    path('delete-pdf/<int:course_id>/<str:pdf_type>/', views_course.delete_pdf, name='delete_pdf'),
    path('delete-module-pdf/<int:module_id>/<str:pdf_type>/', views_course.delete_module_pdf, name='delete_module_pdf'),
    
    # Cart functionality
    path('cart/add/<int:course_id>/', views_course.add_to_cart, name='add_to_cart'),
    path('cart/', views_course.view_cart, name='view_cart'),
    path('cart/remove/<int:course_id>/', views_course.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views_course.checkout, name='checkout'),
    
    # Progress and certificate management
    path('course/<int:course_id>/complete/', views_course.complete_course, name='complete_course'),
    path('course/<int:course_id>/recalculate_progress/', views_course.recalculate_progress, name='recalculate_progress'),
    path('course/<int:course_id>/generate_certificate/', views_course.generate_certificate, name='generate_certificate'),
    path('certificate/<int:certificate_id>/download/', views_course.download_certificate, name='download_certificate'),
    
    # Analytics and statistics
    path('course/<int:course_id>/statistics/', views_course.course_statistics, name='course_statistics'),
    
    # Search and recommendations
    path('search/', views_course.search_courses, name='search_courses'),
    path('course/<int:course_id>/recommendations/', views_course.course_recommendations, name='course_recommendations'),
    
    # Wishlist functionality
    path('course/<int:course_id>/add-to-wishlist/', views_course.add_to_wishlist, name='add_to_wishlist'),
    path('course/<int:course_id>/remove-from-wishlist/', views_course.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views_course.view_wishlist, name='view_wishlist'),
    
    # Discussion system
    path('course/<int:course_id>/add-comment/', views_course.add_course_comment, name='add_course_comment'),
    path('comment/<int:comment_id>/reply/', views_course.add_comment_reply, name='add_comment_reply'),
    path('comment/<int:comment_id>/like/', views_course.like_comment, name='like_comment'),
    path('subcomment/<int:subcomment_id>/like/', views_course.like_subcomment, name='like_subcomment'),
]
