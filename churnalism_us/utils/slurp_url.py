import sys
import logging

import requests

from django.core.cache import cache


def slurp_url(url, use_cache=False):
    def _slurp_url(url):
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.21 (KHTML, like Gecko) Chrome/19.0.1041.0 Safari/535.21'}, config={'verbose': sys.stderr})
        if resp.status_code == 200:
            return resp.content.decode('utf-8', 'ignore')
        else:
            logging.error('Unexpected status ({status}) for ({url})'.format(url=url, status=resp.status_code))
            return None

    cache_key = 'slurp_url:' + url
    if use_cache == True:
        cached_content = cache.get(cache_key)
        if cached_content is not None:
            return cached_content

    content = _slurp_url(url)

    if use_cache == True and content is not None:
        cache.set(cache_key, content)

    return content


