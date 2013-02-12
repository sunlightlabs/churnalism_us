from django.conf import settings

def absolutestaticurl(request):
    return {'ABSOLUTE_STATIC_URL': request.build_absolute_uri(settings.STATIC_URL)}

