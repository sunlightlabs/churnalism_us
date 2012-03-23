from apiproxy.models import SearchDocument
from django import template

register = template.Library()

@register.simple_tag
def latest(number_latest):
    t = template.loader.get_template('apiproxy/latest_churns.html')
    return t.render(template.Context({'latest': SearchDocument.objects.all().order_by('-updated')[:number_latest]}))
 
