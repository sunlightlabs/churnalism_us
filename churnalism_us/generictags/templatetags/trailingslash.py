from django.template import Library

register = Library()

def trailingslash(strval, expected):
    if expected:
        return strval.rstrip('/') + '/'
    else:
        return strval.rstrip('/')

register.filter('trailingslash', trailingslash)


