def baseurl(request):
    return {'BASE_URL': request.build_absolute_uri('')}

