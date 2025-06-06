from django.core.management.base import BaseCommand
from django.utils import timezone
from website.models import Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send scheduled meeting notifications that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending all unsent notifications regardless of scheduled time',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        now = timezone.now()
        
        if force:
            # Get all unsent notifications
            notifications = Notification.objects.filter(sent=False)
            self.stdout.write(self.style.WARNING(f'Force sending {notifications.count()} unsent notifications'))
        else:
            # Get notifications that are scheduled to be sent now or in the past
            notifications = Notification.objects.filter(sent=False, scheduled_time__lte=now)
            self.stdout.write(self.style.SUCCESS(f'Found {notifications.count()} notifications to send'))
        
        sent_count = 0
        error_count = 0
        
        for notification in notifications:
            try:
                self.stdout.write(f'Sending notification {notification.id} - {notification}')
                success = notification.send()
                
                if success:
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Successfully sent notification {notification.id}'))
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Failed to send notification {notification.id}'))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error sending notification {notification.id}: {str(e)}'))
                logger.error(f'Error sending notification {notification.id}: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} notifications with {error_count} errors'))
