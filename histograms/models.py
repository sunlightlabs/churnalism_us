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
        if norm_coeff is None:
            agg = self.bins.aggregate(total_mass=Sum('mass'))
            return agg['total_mass']
        else:
            return self.norm_coeff

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

