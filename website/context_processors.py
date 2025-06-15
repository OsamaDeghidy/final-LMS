from website.models import Category, Notification

def categories_processor(request):
    """
    Context processor that adds all categories to the template context.
    This makes the categories available in all templates.
    """
    return {
        'categories': Category.objects.filter(name__isnull=False).exclude(name='').order_by('name')
    }

def notifications_processor(request):
    """
    Context processor that adds unread notification count to the template context.
    This makes the notification count available in all templates.
    """
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.get_unread_count(request.user)
    
    return {
        'unread_notification_count': unread_count
    }
