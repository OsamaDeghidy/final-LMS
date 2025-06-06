from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from website.models import Meeting, Notification, Profile, School
from django.core import mail
from django.conf import settings
from website.management.commands.send_meeting_notifications import Command


class MeetingNotificationTests(TestCase):
    """Test cases for the meeting notification system"""
    
    def setUp(self):
        """Set up test data"""
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
            phone="123456789",
            email="school@test.com"
        )
        
        # Create users
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@test.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@test.com",
            password="testpass123"
        )
        
        # Create profiles
        Profile.objects.create(
            user=self.user1,
            name="Test User 1",
            email="user1@test.com",
            phone="123456789",
            status="Teacher"
        )
        Profile.objects.create(
            user=self.user2,
            name="Test User 2",
            email="user2@test.com",
            phone="987654321",
            status="Student"
        )
        
        # Create a meeting
        self.meeting = Meeting.objects.create(
            title="Test Meeting",
            description="Test Description",
            meeting_type="NORMAL",
            start_time=timezone.now() + timedelta(days=2),
            duration=60,
            school=self.school,
            creator=self.user1
        )
        
        # Add participant
        self.meeting.participant_set.create(user=self.user2)
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.create_for_meeting(
            meeting=self.meeting,
            notification_type="DAY_BEFORE",
            message="Test notification message"
        )
        
        self.assertEqual(notification.meeting, self.meeting)
        self.assertEqual(notification.notification_type, "DAY_BEFORE")
        self.assertEqual(notification.message, "Test notification message")
        self.assertEqual(notification.recipients.count(), 2)  # Creator + 1 participant
        self.assertFalse(notification.sent)
    
    def test_send_notification(self):
        """Test sending a notification"""
        # Create a notification
        notification = Notification.create_for_meeting(
            meeting=self.meeting,
            notification_type="DAY_BEFORE",
            message="Test notification message"
        )
        
        # Send the notification
        result = notification.send()
        
        # Check that the notification was sent
        self.assertTrue(result)
        self.assertTrue(notification.sent)
        self.assertIsNotNone(notification.sent_at)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "إشعار اجتماع: تذكير قبل يوم - Test Meeting")
        self.assertEqual(len(mail.outbox[0].to), 2)  # Both users should receive the email
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create notifications
        notification1 = Notification.create_for_meeting(
            meeting=self.meeting,
            notification_type="DAY_BEFORE",
            message="Test notification 1"
        )
        notification2 = Notification.create_for_meeting(
            meeting=self.meeting,
            notification_type="HOUR_BEFORE",
            message="Test notification 2"
        )
        
        # Mark one as read for user1
        notification1.is_read = True
        notification1.save()
        
        # Check unread count for user1
        self.assertEqual(Notification.get_unread_count(self.user1), 1)
        
        # Check unread count for user2
        self.assertEqual(Notification.get_unread_count(self.user2), 2)
    
    def test_management_command(self):
        """Test the management command for sending notifications"""
        # Create a notification scheduled for now
        notification = Notification.create_for_meeting(
            meeting=self.meeting,
            notification_type="DAY_BEFORE",
            message="Test notification message",
            scheduled_time=timezone.now() - timedelta(minutes=5)  # 5 minutes ago
        )
        
        # Run the command
        command = Command()
        command.handle()
        
        # Refresh the notification from the database
        notification.refresh_from_db()
        
        # Check that the notification was sent
        self.assertTrue(notification.sent)
        self.assertIsNotNone(notification.sent_at)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
