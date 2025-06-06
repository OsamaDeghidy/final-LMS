from django.urls import path
from . import meeting_views

urlpatterns = [
    path('meetings/', meeting_views.meeting_list, name='meeting_list'),
    path('meetings/create/', meeting_views.meeting_create, name='meeting_create'),
    path('meetings/<int:pk>/', meeting_views.meeting_detail, name='meeting_detail'),
    path('meetings/<int:pk>/update/', meeting_views.meeting_update, name='meeting_update'),
    path('meetings/<int:pk>/delete/', meeting_views.meeting_delete, name='meeting_delete'),
    path('meetings/<int:pk>/mark-attendance/', meeting_views.mark_attendance, name='mark_attendance'),
    path('meetings/<int:pk>/mark-exit/', meeting_views.mark_exit, name='mark_exit'),
    path('my-meetings/', meeting_views.my_meetings, name='my_meetings'),
    path('meeting-notifications/', meeting_views.notifications, name='meeting_notifications'),
]
