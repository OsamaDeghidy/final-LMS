from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key
    Usage: {{ my_dict|get_item:"key_name" }}
    """
    if dictionary is None:
        return None
    
    try:
        return dictionary.get(key)
    except (AttributeError, KeyError, TypeError):
        try:
            # Try accessing as an attribute
            return getattr(dictionary, key)
        except (AttributeError, TypeError):
            return None
