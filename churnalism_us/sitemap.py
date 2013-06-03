from django.core.urlresolvers import reverse
from django.contrib.sitemaps import Sitemap

class GeneralSitemap(Sitemap):
    def items(self):
        return [
            'about',
            'contact',
            'downloads',
            'sidebyside-search-page'
        ]

    def location(self, page):
        return reverse(page)

