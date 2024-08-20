import os
from django import template

register = template.Library()

@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)

@register.filter
def filename(value):
    return os.path.basename(value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_nested_item(dictionary, key):
    keys = key.split('.')
    for k in keys:
        if isinstance(dictionary, dict):
            dictionary = dictionary.get(k)
        else:
            return None
    return dictionary
