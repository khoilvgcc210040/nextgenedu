import os
from django import template
import datetime
from urllib.parse import unquote, urlparse, urlunparse

register = template.Library()

@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)

@register.filter
def filename(value):
    return os.path.basename(value)

@register.filter(name='basename')
def basename(file_url):
    try:
        path = urlparse(file_url).path
        file_name = os.path.basename(path)
        return unquote(file_name)
    except Exception:
        return "Unknown File"
    
@register.filter(name='url_https')
def url_https(url):
    if not url:
        return ''
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'http':
        secure_url = urlunparse(('https',) + parsed_url[1:])
        return secure_url
    return url

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

@register.filter
def format_duration(value):
    if isinstance(value, datetime.timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02}'
    return value
