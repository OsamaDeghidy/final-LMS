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
    # Live meeting URLs
    path('meetings/<int:pk>/live-room/', meeting_views.meeting_live_room, name='meeting_live_room'),
    path('meetings/<int:pk>/start-live/', meeting_views.start_live_meeting, name='start_live_meeting'),
    path('meetings/<int:pk>/end-live/', meeting_views.end_live_meeting, name='end_live_meeting'),
    path('meetings/<int:pk>/send-chat/', meeting_views.send_chat_message, name='send_chat_message'),
    path('meetings/<int:pk>/get-chat/', meeting_views.get_chat_messages, name='get_chat_messages'),
    path('my-meetings/', meeting_views.my_meetings, name='my_meetings'),
    path('meeting-notifications/', meeting_views.notifications, name='meeting_notifications'),
]
