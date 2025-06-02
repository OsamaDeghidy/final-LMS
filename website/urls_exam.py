from django.urls import path
from . import exam_views

urlpatterns = [
    # Teacher exam management
    path('exams/', exam_views.teacher_exams, name='teacher_exams'),  # For when no course is selected
    path('exams/course/<int:course_id>/', exam_views.teacher_exams, name='teacher_exams_course'),
    path('course/<int:course_id>/exams/create/', exam_views.create_exam, name='create_exam'),
    path('exam/<int:exam_id>/edit/', exam_views.edit_exam, name='edit_exam'),
    path('exam/<int:exam_id>/delete/', exam_views.delete_exam, name='delete_exam'),
    
    # Question management
    path('exam/<int:exam_id>/questions/add/', exam_views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', exam_views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', exam_views.delete_question, name='delete_question'),
    path('exam/<int:exam_id>/questions/reorder/', exam_views.reorder_questions, name='reorder_questions'),
    
    # Student exam views
    path('student/exams/', exam_views.student_exams_list, name='student_exams_list'),
    path('course/<int:course_id>/exams/', exam_views.student_exams, name='student_course_exams'),
    path('exam/<int:exam_id>/take/', exam_views.take_exam, name='take_exam'),
    path('exam-attempt/<int:attempt_id>/submit/', exam_views.submit_exam, name='submit_exam'),
    path('exam-attempt/<int:attempt_id>/results/', exam_views.exam_results, name='exam_results'),
    
    # Teacher grading views
    path('exam/<int:exam_id>/attempts/', exam_views.teacher_exam_attempts, name='teacher_exam_attempts'),
    path('exam-attempt/<int:attempt_id>/grade/', exam_views.grade_short_answers, name='grade_short_answers'),
]
