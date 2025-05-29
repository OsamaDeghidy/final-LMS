from django import template
from django.template.defaultfilters import stringfilter
from website.models import Category

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)

@register.filter
def format_duration(seconds):
    """
    Formats seconds into a readable duration (MM:SS).
    Usage: {{ seconds|format_duration }}
    """
    if not seconds:
        return "00:00"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    return f"{minutes:02d}:{remaining_seconds:02d}"


@register.simple_tag
def get_categories():
    """
    Returns all categories for use in navigation menu.
    Usage: {% get_categories as categories %}
    """
    return Category.objects.all()
