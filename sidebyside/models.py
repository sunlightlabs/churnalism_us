from django.db import models

from apiproxy.models import Match
from histograms.models import (Histogram, HistogramBin,
                               histogram_metaclass, histogram_bin_metaclass)

from django.conf import settings

VisibleMatches = Match.objects.filter(overlapping_characters__gte=settings.SIDEBYSIDE['minimum_coverage_chars'],
                                      percent_churned__gte=settings.SIDEBYSIDE['minimum_coverage_pct'])

class MatchCurveHistogram(Histogram):
    __metaclass__ = histogram_metaclass(max_digits=20,
                                        decimal_places=0,
                                        normalized=False)
    doc_type = models.IntegerField(null=True)

class MatchCurveHistogramBin(HistogramBin):
    __metaclass__ = histogram_bin_metaclass(MatchCurveHistogram)

