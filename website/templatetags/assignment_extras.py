from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to access dictionary items by key
    Usage: {{ my_dict|get_item:key_variable }}
    """
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    """
    Template filter to access object attributes
    Usage: {{ my_obj|get_attr:'attribute_name' }}
    """
    return getattr(obj, attr, None)
