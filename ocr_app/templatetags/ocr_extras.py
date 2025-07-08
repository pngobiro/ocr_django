# ocr_app/templatetags/ocr_extras.py
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
        
@register.filter
def sub(value, arg):
    """Subtract the argument from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''
