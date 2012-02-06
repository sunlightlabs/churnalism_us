import requests

def slurp_url(url, use_cache=False):
    def _slurp_url(url):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.content.decode('utf-8')
        else:
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
