# Create your views here.

import json

from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import View

class HistogramJSONView(View):
    histogram_model = None

    def get(self, request, *args, **kwargs):
        if self.histogram_model is None:
            raise ValueError(u"You must pass a histogram_model kwarg to HistogramJSONView.as_view")

        filter_params = kwargs or request.GET.dict()
        filter_params = {key: None if value == u'' else value
                         for (key, value) in filter_params.items()}
        histograms = self.histogram_model.objects.filter(**filter_params)

        if len(histograms) == 0:
            raise HttpResponseNotFound()
        elif len(histograms) > 1:
            raise ValueError(u"Multiple histograms for filter parameters: {kw}".format(kw=kwargs))

        histo = {
            'bins': [ { 'ordinal_position': b.ordinal_position,
                        'label': b.label,
                        'mass': float(b.mass) }
                     for b in histograms[0].bin_iterator()],
            'title': histograms[0].title,
            'mass_axis_label': histograms[0].mass_axis_label,
            'bin_axis_label': histograms[0].bin_axis_label,
            'total_mass': float(histograms[0].total_mass()),
            'normalized': histograms[0].normalized
        }

        return HttpResponse(json.dumps(histo, indent=2), content_type='application/json')
