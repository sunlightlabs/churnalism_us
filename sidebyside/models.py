from django.db import models

from histograms.models import (Histogram, HistogramBin,
                               histogram_metaclass, histogram_bin_metaclass)

class MatchCurveHistogram(Histogram):
    __metaclass__ = histogram_metaclass(max_digits=20,
                                        decimal_places=0,
                                        normalized=True)
    doc_type = models.IntegerField(null=True)

class MatchCurveHistogramBin(HistogramBin):
    __metaclass__ = histogram_bin_metaclass(MatchCurveHistogram)

