from django import template
from builtins import getattr as builtin_getattr  # 👈 safe import

register = template.Library()

@register.filter
def getattr(obj, attr):
    try:
        return builtin_getattr(obj, attr)
    except AttributeError:
        return ''