import re
import urlparse
from django.conf import settings

UrlBlacklist = settings.APIPROXY.get('blacklisted_news_urls', [])
CompiledUrlBlacklist = [re.compile(pattern)
                        for pattern in UrlBlacklist]

def check_url_blacklist(url):
    host = urlparse.urlsplit(url).netloc
    for pattern in CompiledUrlBlacklist:
        m = pattern.match(host)
        if m is not None:
            return (True, m)
    return (False, None)

