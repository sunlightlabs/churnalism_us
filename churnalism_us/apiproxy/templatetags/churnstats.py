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
                      .filter(~Q(search_document__title=''))
                      .order_by('-updated')[:20])

    for rm in recent_matches:
        if rm.search_document_id not in dedupe and len(churns) < number_latest:
            churns.append({'percent': rm.percent_churned, 
                           'title': rm.search_document.title, 
                           'text': rm.search_document.text, 
                           'uuid': rm.search_document.uuid,
                           'doctype': rm.matched_document.doc_type,
                           'docid': rm.matched_document.doc_id})
            dedupe.append(rm.search_document_id)

    return t.render(template.Context({'latest': churns[:number_latest] }))
 
@register.simple_tag
def most_read(number_viewed):
    t = template.loader.get_template('apiproxy/most_viewed.html')
    churns = pickle.load(open(settings.PROJECT_ROOT + '/analytics/management/commands/most_read.dat'))
    """
    data = get_most_viewed()
    for d in data:
        params = d.split('_')
        if len(params) > 2: #should have a uuid, doctype and doc id
            uuid = params[0]
            doctype = params[1]
            docid = params[2]
            
            try:
                searchdoc = SearchDocument.objects.get(uuid=uuid)
                matchdoc = MatchedDocument.objects.get(doc_id=docid, doc_type=doctype)
                match = Match.objects.filter(search_document=searchdoc, matched_document=matchdoc, percent_churned__gte=settings.SIDEBYSIDE.get('minimum_coverage_pct', 0), overlapping_characters__gte=settings.SIDEBYSIDE.get('minimum_coverage_chars', 0)).order_by('-percent_churned')[:20]
                if len(match) > 0:
                    match = match[0]

                    churns.append({'percent': match.percent_churned, 
                                'title':searchdoc.title, 
                                'text': searchdoc.text, 
                                'uuid': searchdoc.uuid,
                                'doctype': matchdoc.doc_type,
                                'docid': matchdoc.doc_id})
            except MatchedDocument.DoesNotExist:
                continue
            except SearchDocument.DoesNotExist:
                continue
    """
    return t.render(template.Context({'viewed': churns[:number_viewed]}))
 
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
 
