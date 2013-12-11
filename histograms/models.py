# -*- coding: utf-8 -*-
"""
The Histogram model is a base class for creating your own histogram models.
To allow your Histogram subclass to provide sufficient precision, the digit
and decimal widths of the column types are deferred to a metaclass that is
created by histogram_metaclass() and histogram_bin_metaclass().

At issue is whether you want your data stored in normalized form, where each
bin represents a proportion of the whole and the sum is 1 versus the
denormalized form where each bin represents some (possibly very large) tally.

To use Histogram for a normalized histogram:
    class MyHistogram(Histogram):
        __metaclass__ = histogram_metaclass(max_digits=22,
                                            decimal_places=21,
                                            normalized=True)
    class MyHistogramBin(HistogramBin):
        __metaclass__ = histogram_bin_metaclass(MyHistogram)

To use Histogram for a denormalized histogram, where you know your data will
never represent more than 100 items:
    class YourHistogram(Histogram):
        __metaclass__ = histogram_metaclass(max_digits=3,
                                            decimal_places=0,
                                            normalized=False)
    class YourHistogramBin(HistogramBin):
        __metaclass__ = histogram_bin_metaclass(Histogram)

If the HistogramBin subclasses seem like mostly boiler-plate, that's because
they are in this case. The bin subclass is kept separate from the histogram
subclass to allow your own customizations.
"""

from __future__ import division, print_function

from django.db import models

import math
import decimal

from operator import isCallable
from collections import Counter

def histogram_metaclass(max_digits, decimal_places, normalized):
    def _histogram_metaclass(clsname, parents, attrs):
        attrs.update({
            'norm_coeff': models.DecimalField(null=True,
                                              max_digits=max_digits,
                                              decimal_places=decimal_places,
                                              help_text="Coefficient for normalized histograms."),
            'max_digits': max_digits,
            'decimal_places': decimal_places,
            'normalized': normalized
        })
        return type(clsname, parents, attrs)
    return _histogram_metaclass

def histogram_bin_metaclass(histogram_class):
    def _histogram_bin_metaclass(clsname, parents, attrs):
        if histogram_class.normalized == True:
            decimal_places = histogram_class.max_digits - 1
        else:
            decimal_places = histogram_class.decimal_places

        attrs.update({
            'mass': models.DecimalField(null=False,
                                        max_digits=histogram_class.max_digits,
                                        decimal_places=decimal_places,
                                        help_text='Proportion of total histogram mass'),
            'histogram': models.ForeignKey(histogram_class, related_name='bins')
        })
        return type(clsname, parents, attrs)
    return _histogram_bin_metaclass

class Histogram(models.Model):
    normalized = False
    max_digits = 20

    class Meta:
        abstract = True

    title = models.CharField(null=False,
                             max_length=200)
    mass_axis_label = models.CharField(null=False,
                                       max_length=200,
                                       help_text="Dependent axis label")
    bin_axis_label = models.CharField(null=False,
                                      max_length=200,
                                      help_text="Independent axis label")

    def from_sequence(self, seq, bincmp=None):
        """
        Expects a sequence of 2-tuples of the form (bin, mass)
        where mass >= 0. If you want a pure count histogram, pass
        in 1 for all mass values.
        """
        total = decimal.Decimal(0)
        cntr = Counter()
        for (bin, mass) in seq:
            if mass < 0:
                raise ValueError(u"The mass value ({}) must be >= 0".format(unicode(mass)))
            mass = decimal.Decimal(mass)
            cntr += Counter({bin: mass})
            total += mass

        self.norm_coeff = total if self.normalized == True else None
        self.bins.all().delete()

        sorted_bins = sorted(cntr.keys(), cmp=(bincmp or cmp))
        for (idx, bin) in enumerate(sorted_bins):
            mass = cntr[bin]
            if self.normalized == True and total > 0:
                mass = decimal.Decimal(round(mass / total,
                                             self.max_digits - 1))
            try:
                self.bins.create(histogram=self,
                                 ordinal_position=idx,
                                 mass=mass,
                                 label=unicode(bin))
            except decimal.InvalidOperation as e:
                import ipdb; ipdb.set_trace()
        self.save()

    def total_mass(self):
        if self.norm_coeff is None:
            agg = self.bins.aggregate(total_mass=models.Sum('mass'))
            return agg['total_mass'] or 0
        else:
            return self.norm_coeff

    def bin_iterator(self):
        return self.bins.order_by('ordinal_position')

class HistogramBin(models.Model):
    class Meta:
        abstract = True
        unique_together = ('histogram', 'ordinal_position')
        unique_together = ('histogram', 'label')
        ordering = ['ordinal_position']

    ordinal_position = models.IntegerField(null=False)
    label = models.CharField(max_length=200)

    def denormalized_mass(self):
        return self.mass / (self.histogram.norm_coeff or 1)

    def normalized_mass(self):
        if self.histogram.norm_coeff is None:
            return self.mass / self.histogram.total_mass()
        else:
            return self.mass

