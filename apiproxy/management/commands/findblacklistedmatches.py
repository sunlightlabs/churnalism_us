from __future__ import print_function

import sys
import progressbar
import unicodecsv as csv
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from apiproxy.models import SearchDocument
from apiproxy.blacklist import UrlBlacklist, check_url_blacklist

class Command(BaseCommand):
    help = 'Searches through SearchDocuments for articles from blacklisted sites.'
    args = ''

    def handle(self, *args, **options):
        if len(UrlBlacklist) == 0:
            raise CommandError("No sites are blacklisted.\nDouble-check that you've configured settings.APIPROXY['blacklisted_news_urls']")

        docs_with_url = SearchDocument.objects.filter(~Q(url=''), url__isnull=False)
        cnt = docs_with_url.count()
        chunk_size = 1000
        offset = 0


        progress = progressbar.ProgressBar(maxval=cnt,
                                           widgets=[
                                               progressbar.widgets.AnimatedMarker(),
                                               '  ',
                                               progressbar.widgets.Counter(),
                                               '/{0}  '.format(cnt),
                                               progressbar.widgets.Percentage(),
                                               '  ',
                                               progressbar.widgets.ETA(),
                                           ])
        progress.start()

        ordered_docs = docs_with_url.order_by('uuid')

        wrtr = csv.writer(sys.stdout)
        wrtr.writerow(['MatchCount', 'UUID', 'URL'])
        while True:
            chunk = ordered_docs[offset:offset+chunk_size]
            processed = 0
            for doc in chunk:
                (url_is_blacklisted, match) = check_url_blacklist(doc.url)
                if url_is_blacklisted:
                    wrtr.writerow([doc.match_set.count(),
                                   doc.uuid,
                                   doc.url])
                processed += 1
                progress.update(offset + processed)
            if processed == 0:
                break
            offset += chunk_size

        progress.finish()

