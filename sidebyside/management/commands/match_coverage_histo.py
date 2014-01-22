from __future__ import division, print_function

import math

from operator import itemgetter
from decimal import Decimal
from django.db import connection
from django.db.models import Count, Q
from django.core.management.base import BaseCommand, CommandError
from natsort import natsorted, natsort_key
from apiproxy.models import SearchDocument, MatchedDocument, Match
from sidebyside.models import MatchPercentHistogram, MatchCharsHistogram
from utils.batched_results import batched_results

from django.conf import settings

def power_of_ten_floor(n):
    """
    Sets all but the most significant digit to zero.

    For example:
    >>> power_of_ten_floor(12517)
    10000
    >>> power_of_ten_floor(-417.6)
    -400.0
    >>> from decimal import Decimal
    >>> power_of_ten_floor(Decimal('616161'))
    Decimal('600000')
    """
    n_type = type(n)
    pow10 = n_type(pow(10, math.floor(math.log10(abs(n)))))
    return n_type(n_type(round(n / pow10)) * pow10)

class Command(BaseCommand):
    help = 'Generates histogram data for match overlap.'
    args = ''

    def handle(self, *args, **options):
        self.character_histogram()
        self.percentage_histogram()

    def character_histogram(self):
        cnt = MatchCharsHistogram.objects.count()
        if cnt == 0:
            chars_histo = MatchCharsHistogram.objects.create()
        elif cnt > 1:
            raise CommandError(u"Too many MatchCharsHistogram objects found in the database.")
        else:
            chars_histo = MatchCharsHistogram.objects.all()[0]

        chars_histo.title = "Number of Matches by Overlapping Characters"
        chars_histo.bin_axis_label = "Overlapping Characters"
        chars_histo.mass_axis_label = "Number of Matches"
        chars_histo.save()

        chars_histo.from_sequence(((power_of_ten_floor(grp['overlapping_characters']), 1)
                                   for grp in (Match.objects
                                                    .filter(overlapping_characters__lte=5000)
                                                    .values('overlapping_characters'))
                                   if grp['overlapping_characters'] is not None))

    def percentage_histogram(self):
        cnt = MatchPercentHistogram.objects.count()
        if cnt == 0:
            pct_histo = MatchPercentHistogram.objects.create()
        elif cnt > 1:
            raise CommandError(u"Too many MatchPercentHistogram objects found in the database.")
        else:
            pct_histo = MatchPercentHistogram.objects.all()[0]

        # E.g. [ {'cnt' 743277, 'pct': Decimal('0')}, ... ]
        aggs = list(Match.objects
                         .filter(percent_churned__lt=15)
                         .extra(select={'pct': 'round(percent_churned)'})
                         .values('pct')
                         .order_by('pct')
                         .annotate(cnt=Count('pk')))
        aggs.sort(key=itemgetter('pct'))

        pct_histo.title = "Number of Matches by Overlap Percentage"
        pct_histo.bin_axis_label = "Overlap Percentage"
        pct_histo.mass_axis_label = "Number of Matches"
        pct_histo.save()

        def extract_pair(grp):
            pct = grp['pct']
            try:
                pct = u"{}%".format(grp['pct'])
            except (ValueError, TypeError):
                pass
            return (pct, grp['cnt'])

        pct_histo.from_sequence((extract_pair(grp)
                                 for grp in aggs),
                                bincmp=lambda a, b: cmp(natsort_key(a), natsort_key(b)))

