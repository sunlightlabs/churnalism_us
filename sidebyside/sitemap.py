from django.core.urlresolvers import reverse
from django.contrib.sitemaps import Sitemap
from apiproxy.models import Match
from django.conf import settings

class SidebysideSitemap(Sitemap):
    def items(self):
        minimum_pct = settings.SIDEBYSIDE.get('minimum_coverage_pct', 1)
        minimum_chars = settings.SIDEBYSIDE.get('minimum_coverage_chars', 180)
        return Match.objects.filter(percent_churned__gte=minimum_pct,
                                    overlapping_characters__gte=minimum_chars)

    def location(self, match):
        return reverse('sidebyside-generic', args=(
            match.search_document.uuid,
            match.matched_document.doc_type,
            match.matched_document.doc_id))

    def lastmod(self, obj):
        return obj.updated

