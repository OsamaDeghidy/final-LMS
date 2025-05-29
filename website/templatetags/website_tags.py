from django import template
from django.template.defaultfilters import stringfilter
from website.models import Category

register = template.Library()

@register.simple_tag
def get_categories():
    """
    Returns all categories for use in navigation menu.
    Usage: {% get_categories as categories %}
    """
    return Category.objects.all()
