import re
from urlparse import urlparse
from django import template

register = template.Library()

@register.filter
def domain(url):
    if not url:
        return url

    (scheme, netloc, path, params, query, frag) = urlparse(url)
    if not netloc:
        return url

    return re.sub('/:\d+$', '', netloc)
