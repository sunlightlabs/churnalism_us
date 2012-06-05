from apiproxy.models import SearchDocument, Match
from django import template
from django.conf import settings
from django.db.models import Q

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
                      .filter(~Q(search_document__title=''))
                      .order_by('-percent_churned')[:20])
    for rm in recent_matches:
        if rm.search_document_id not in dedupe and len(churns) < number_latest:
            churns.append({'percent': rm.percent_churned, 
                           'title': rm.search_document.title, 
                           'text': rm.search_document.text, 
                           'uuid': rm.search_document.uuid,
                           'doctype': rm.matched_document.doc_type,
                           'docid': rm.matched_document.doc_id})
            dedupe.append(rm.search_document_id)

    return t.render(template.Context({'latest': churns }))
 
@register.simple_tag
def most_read(number_viewed):
    t = template.loader.get_template('apiproxy/most_viewed.html')
    matches = (Match.objects
               .filter(percent_churned__gte=settings.SIDEBYSIDE.get('minimum_coverage_pct', 0))
               .filter(overlapping_characters__gte=settings.SIDEBYSIDE.get('minimum_coverage_chars', 0))
               .filter(~Q(search_document__url=''))
               .filter(~Q(search_document__title=''))
               .order_by('-number_matches')[:20])
    churns = []
    dedupe = []
    for m in matches:
        if m.search_document_id not in dedupe and len(churns) < number_viewed:
            churns.append({'percent': m.percent_churned, 
                           'title':m.search_document.title, 
                           'text': m.search_document.text, 
                           'uuid': m.search_document.uuid,
                           'doctype': m.matched_document.doc_type,
                           'docid': m.matched_document.doc_id})
            dedupe.append(m.search_document_id)

    return t.render(template.Context({'viewed': churns}))
 
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
 
