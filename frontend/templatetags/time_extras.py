# frontend/templatetags/time_extras.py

from django import template

register = template.Library()

@register.filter
def time_display(value):
    """
    Convert an integer minute-of-day (e.g. 540) into HH:MM format (e.g. '09:00').
    """
    if not isinstance(value, int):
        return value
    hour = value // 60
    minute = value % 60
    return f"{hour:02d}:{minute:02d}"
