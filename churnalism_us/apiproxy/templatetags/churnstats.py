from apiproxy.models import SearchDocument, Match
from django import template

register = template.Library()

@register.simple_tag
def latest(number_latest):
    t = template.loader.get_template('apiproxy/latest_churns.html')
    return t.render(template.Context({'latest': SearchDocument.objects.all().order_by('-updated')[:number_latest]}))
 
@register.simple_tag
def most_read(number_viewed):
    t = template.loader.get_template('apiproxy/most_viewed.html')
    matches = Match.objects.all().order_by('-number_matches')
    docs = []
    for m in matches:
        if m.search_document not in docs and len(docs) < number_viewed :
            docs.append(m.search_document)

    return t.render(template.Context({'viewed': docs}))
 
@register.simple_tag
def most_shared(number_shared):
    t = template.loader.get_template('apiproxy/most_shared.html')
    return t.render(template.Context({'shared': SearchDocument.objects.exclude(times_shared=None).order_by('-times_shared')[:number_shared]}))
 
