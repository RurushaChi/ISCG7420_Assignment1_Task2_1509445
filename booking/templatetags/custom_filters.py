# booking/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """Split a string into a list using the given delimiter."""
    if not value:
        return []
    return value.split(delimiter)
