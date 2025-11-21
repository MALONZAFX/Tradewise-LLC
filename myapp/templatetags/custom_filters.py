from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get dictionary value by key in templates"""
    if not isinstance(dictionary, dict):
        # If it's not a dictionary, return None or the original value
        return None
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0