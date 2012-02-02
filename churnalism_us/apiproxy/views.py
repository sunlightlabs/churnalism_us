import json

import readability
import lxml
from django.http import HttpResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import superfastmatch
from sidebyside.views import render_text, slurp_url


def document_list(request):
    pass


def document(request, doctype, docid):
    sfm = superfastmatch.DjangoClient()
    response = sfm.document(doctype, docid)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


@csrf_exempt
def search(request, doctype=None):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    text = request.POST.get('text')
    url = request.POST.get('url')
    title = None
    if text in ('', None) and url not in ('', None):
        html = slurp_url(url)

        doc = readability.Document(html)
        title = doc.short_title()
        content_dom = lxml.html.fromstring(doc.summary())
        text = render_text(content_dom)

    sfm = superfastmatch.DjangoClient()
    response = sfm.search(text, doctype)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        response['text'] = text
        if title:
            response['title'] = title
        for row in response['documents']['rows']:
            doc = sfm.document(row['doctype'], row['docid'])
            row['text'] = doc['text']
        return HttpResponse(json.dumps(response, indent=2), content_type='application/json')



