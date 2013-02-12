import lxml
from .slurp_url import slurp_url
from .textextract import readability_extract

def fetch_and_clean(url):
    html = slurp_url(url, use_cache=True)
    if not html:
        raise Exception('Failed to fetch {0}'.format(url))

    htmldoc = lxml.html.fromstring(html)
    to_remove = [e
                 for e in htmldoc.iterdescendants()
                 if e.tag == lxml.etree.Comment
                 or e.tag == 'script'
                 or e.tag == 'noscript'
                 or e.tag == 'object'
                 or e.tag == 'embed']
    for e in to_remove:
        e.getparent().remove(e)
    html = lxml.html.tostring(htmldoc)

    (title, text) = readability_extract(html)
    return (title, text)


