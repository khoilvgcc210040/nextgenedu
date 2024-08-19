import os
from django import template

register = template.Library()

@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)

@register.filter
def filename(value):
    return os.path.basename(value)
