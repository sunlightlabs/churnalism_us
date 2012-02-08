from django.core.management.base import BaseCommand
from django.db.models import Count
from apiproxy.models import SearchDocument

class Command(BaseCommand):
    help = 'Print out a frequency table of the domains associated with fetched documents.'
    args = ''

    def handle(self, *args, **options):
        counts = (SearchDocument
                  .objects
                  .values('domain')
                  .annotate(cnt=Count('domain'))
                  .order_by('-cnt'))

        for grp in counts:
            print "{cnt!s:>13} {domain}".format(**grp)


