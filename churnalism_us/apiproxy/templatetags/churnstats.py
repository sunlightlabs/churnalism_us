from apiproxy.models import SearchDocument, Match
from django import template

register = template.Library()

@register.simple_tag
def latest(number_latest):
    churns = []
    dedupe = []
    t = template.loader.get_template('apiproxy/latest_churns.html')
    recent_matches = Match.objects.all().order_by('-updated')[:20]
    for rm in recent_matches:
        if rm.search_document not in dedupe and len(churns) < number_latest:
            churns.append({'percent': rm.percent_churned, 'title': rm.search_document.title, 'text': rm.search_document.text, 'uuid': rm.search_document.uuid})
            dedupe.append(rm.search_document)

    return t.render(template.Context({'latest': churns }))
 
@register.simple_tag
def most_read(number_viewed):
    t = template.loader.get_template('apiproxy/most_viewed.html')
    matches = Match.objects.all().order_by('-number_matches')[:20]
    churns = []
    dedupe = []
    for m in matches:
        if m.search_document not in dedupe and len(churns) < number_viewed :
            churns.append({'percent': m.percent_churned, 'title':m.search_document.title, 'text': m.search_document.text, 'uuid': m.search_document.uuid})
            dedupe.append(m.search_document)

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
 
