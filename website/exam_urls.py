from django.urls import path
from . import exam_views

urlpatterns = [
    # Teacher exam management
    path('exams/create/<int:course_id>/', exam_views.create_exam, name='create_exam'),
    path('exams/edit/<int:exam_id>/', exam_views.edit_exam, name='edit_exam'),
    path('exams/delete/<int:exam_id>/', exam_views.delete_exam, name='delete_exam'),
    path('exams/view/<int:exam_id>/', exam_views.view_exam, name='view_exam'),
    
    # Question management
    path('exams/questions/add/<int:exam_id>/', exam_views.add_question, name='add_question'),
    path('exams/questions/edit/<int:question_id>/', exam_views.edit_question, name='edit_question'),
    path('exams/questions/delete/<int:question_id>/', exam_views.delete_question, name='delete_question'),
    path('exams/reorder-questions/<int:exam_id>/', exam_views.reorder_questions, name='reorder_questions'),
    
    # Student exam views
    path('exams/course/<int:course_id>/', exam_views.student_exams, name='student_exams'),
    path('exams/start/<int:exam_id>/', exam_views.start_exam, name='start_exam'),
    path('exams/take/<int:attempt_id>/', exam_views.take_exam, name='take_exam'),
    path('exams/submit/<int:attempt_id>/', exam_views.submit_exam, name='submit_exam'),
    path('exams/autosave/<int:attempt_id>/', exam_views.autosave_exam, name='autosave_exam'),
    path('exams/results/<int:attempt_id>/', exam_views.exam_results, name='exam_results'),
    
    # Teacher grading and results
    path('exams/attempts/<int:exam_id>/', exam_views.teacher_exam_attempts, name='teacher_exam_attempts'),
    path('exams/grade/<int:attempt_id>/', exam_views.grade_short_answers, name='grade_short_answers'),
]
