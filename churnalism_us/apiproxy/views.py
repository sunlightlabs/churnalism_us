"""
These views expose an API that provides a subset of the Superfastmatch 
API. It provides a few opportunities:

    - Enhance search responses by pre-fetching matching documents.
    - Merge fragments in search results.
    - Allow saving of searched document text.
    - Capture rich analytics.
    - Provide another caching layer if needed.

"""

import json

import readability
import lxml
from datetime import datetime
from django.http import (HttpResponse, HttpResponseNotAllowed, 
                         HttpResponseBadRequest, HttpResponseServerError)
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import superfastmatch
from apiproxy.models import SearchDocument
from sidebyside.views import render_text
from utils.slurp_url import slurp_url


def association(request, doctype=None):
    """
    Proxies requests for lists of associations to Superfastmatch.
    """

    sfm = superfastmatch.DjangoClient()
    page = request.GET.get('cursor')
    response = sfm.associations(doctype, page)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


def document_list(request, doctype=None):
    """
    Proxies requests for lists of documents to Superfastmatch.
    """

    sfm = superfastmatch.DjangoClient()
    page = request.GET.get('cursor')
    response = sfm.documents(doctype, page)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


def document(request, doctype, docid):
    """
    Proxies requests for specific documents to Superfastmatch.
    """

    sfm = superfastmatch.DjangoClient()
    response = sfm.document(doctype, docid)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


def reduce_fragments(fragments):
    return fragments


def fetch_and_clean(url):
    try:
        stored_doc = SearchDocument.objects.lookup_by_url(url)
        created = False
    except SearchDocument.DoesNotExist:
        stored_doc = SearchDocument()
        stored_doc.url = url
        created = True

    if created or (datetime.now() - stored_doc.updated) >= settings.DOCUMENT_STALENESS_TIMEOUT:
        html = slurp_url(url)
        if not html:
            if created:
                raise Exception('Failed to fetch {0}'.format(url))
            else:
                return stored_doc

        doc = readability.Document(html)
        cleaned_html = doc.summary()
        content_dom = lxml.html.fromstring(cleaned_html)

        stored_doc.html = html
        stored_doc.title = doc.short_title()
        stored_doc.text = render_text(content_dom)
        stored_doc.save()
        return stored_doc
    else:
        return stored_doc


@csrf_exempt
def search(request, doctype=None):
    """
    Proxies /search/ to Superfastmatch, returning the response with 
    the text of each matching document attached to the row in the 
    result. This will reduce the round-trips on the assumption that
    the user will want to view all of the matches.

    TODO: This should limit the number of documents it preemptively 
          retrieves. How to choose the limit? Let the client specify
          a maximum? Choose which documents to retrieve based on match
          length.
    """

    # `text` and `url` are mutually exclusive. `text` has priority over `url`.
    text = request.POST.get('text') or request.GET.get('text')
    url = request.POST.get('url') or request.GET.get('url')
    title = None
    if not text and not url:
        return HttpResponseBadRequest()

    elif url and not text:
        # Fetch and process the source
        try:
            doc = fetch_and_clean(url)
            text = doc.text
            title = doc.title
        except Exception, e:
            return HttpResponseServerError(str(e))

    # The actual proxying:
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

