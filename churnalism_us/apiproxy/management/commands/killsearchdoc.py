import re
from django.core.management.base import BaseCommand
from apiproxy.models import SearchDocument

class Command(BaseCommand):
    help = 'Delete a SearchDocument instance by URL or UUID.'
    args = '<url or uuid> [ <url or uuid> ... ]'

    def handle(self, *args, **options):
        UUIDPattern = re.compile('^[a-z0-9]{32}$')
        for arg in args:
            uuid_match = UUIDPattern.match(arg)
            if uuid_match is None:
                doc = SearchDocument.objects.lookup_by_url(url=arg)
            else:
                doc = SearchDocument.objects.get(uuid=arg)

            if doc is None:
                print "Not found: {0}".format(arg)

            doc.delete()



