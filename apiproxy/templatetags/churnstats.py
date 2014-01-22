import os
from apiproxy.models import SearchDocument, Match, MatchedDocument
from django import template
from django.conf import settings
from django.db.models import Q
import pickle
register = template.Library()

@register.simple_tag
def latest(number_latest):
    churns = []
    dedupe = []
    t = template.loader.get_template('apiproxy/latest_churns.html')
    recent_matches = (Match.objects
                      .filter(percent_churned__gte=settings.SIDEBYSIDE.get('minimum_coverage_pct', 0))
                      .filter(overlapping_characters__gte=settings.SIDEBYSIDE.get('minimum_coverage_chars', 0))
                      .filter(~Q(search_document__url=''))
                      .filter(search_document__title__isnull=False)
                      .filter(~Q(search_document__title=''))
                      .order_by('-updated')
                      .values('search_document__uuid',
                              'search_document__title')[:20])

    for rm in recent_matches:
        if rm['search_document__uuid'] not in dedupe and len(churns) < number_latest:
            churns.append({'title': rm['search_document__title'],
                           'uuid': rm['search_document__uuid']})
            dedupe.append(rm['search_document__uuid'])

    return t.render(template.Context({'latest': churns[:number_latest] }))

@register.simple_tag
def most_read(number_viewed):
    t = template.loader.get_template('apiproxy/most_viewed.html')
    try:
        with file(os.path.join(settings.PROJECT_ROOT, 'most_read.dat'), 'r') as inf:
            churns = pickle.load(inf)
            return t.render(template.Context({'viewed': churns[:number_viewed]}))
    except IOError:
        return t.render(template.Context({'viewed': []}))

@register.simple_tag
def most_shared(number_shared):
    t = template.loader.get_template('apiproxy/most_shared.html')
    sh = SearchDocument.objects.exclude(times_shared=None).order_by('-times_shared')[:number_shared]
    shared = []
    for s in sh:
        matches = Match.objects.filter(search_document=s)
        if len(matches) > 0:
            shared.append({'percent': matches[0].percent_churned, 'title': s.title, 'text': s.text, 'uuid': s.uuid})
    return t.render(template.Context({'shared': shared }))

