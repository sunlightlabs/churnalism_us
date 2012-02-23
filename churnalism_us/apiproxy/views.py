# -*- coding: utf-8 -*-
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

from operator import itemgetter
from copy import deepcopy
from datetime import datetime
from django.http import (HttpResponse, HttpResponseNotAllowed, 
                         HttpResponseBadRequest, HttpResponseServerError)
from django.core import urlresolvers
from django.shortcuts import get_object_or_404
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
    begin = itemgetter(0)
    origbegin = itemgetter(1)
    length = itemgetter(2)
    end = lambda f: begin(f) + length(f)

    def compare_bounds(a, b):
        if begin(a) == begin(b):
            return end(b) - end(a)
        else:
            return begin(a) - begin(b)

    def subsumes(a, b):
        return begin(a) <= begin(b) and end(b) <= end(a)

    def overlaps(a, b):
        if begin(a) <= begin(b) <= end(a):
            return True
        elif begin(b) <= begin(a) <= end(b):
            return True
        else:
            return False

    frags = deepcopy(fragments)
    frags.sort(cmp=compare_bounds)

    new_frags = []
    while len(frags) > 0:
        a = frags.pop(0)

        if len(frags) == 0:
            new_frags.append(a)
        else:
            while len(frags) > 0:
                b = frags.pop(0)
                if subsumes(a, b):
                    pass # Ignore b
                elif subsumes(b, a):
                    a = deepcopy(b)
                elif overlaps(a, b):
                    a = [min(begin(a), begin(b)),
                         min(origbegin(a), origbegin(b)),
                         max(end(a), end(b)),
                         None] # Neither hash applies
                else:
                    frags = [b] + frags
                    break
            new_frags.append(a)

    return new_frags


def fetch_and_clean(url):
    try:
        stored_doc = SearchDocument.objects.lookup_by_url(url)
        created = False
    except SearchDocument.DoesNotExist:
        stored_doc = SearchDocument()
        stored_doc.url = url
        created = True

    if created or (datetime.now() - stored_doc.updated) >= settings.APIPROXY['document_timeout']:
        html = slurp_url(url)
        print html
        if not html:
            if created:
                raise Exception('Failed to fetch {0}'.format(url))
            else:
                return stored_doc

        doc = readability.Document(html)
        cleaned_html = doc.summary()
        content_dom = lxml.html.fromstring(cleaned_html)

        stored_doc.src = html
        stored_doc.title = doc.short_title().strip()
        stored_doc.text = render_text(content_dom).strip().encode('utf-8', 'replace').decode('utf-8')
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
    uuid = request.POST.get('uuid') or request.GET.get('uuid')

    title = None
    if not text and not url and not uuid:
        return HttpResponseBadRequest()

    elif url and not text:
        # Fetch and process the source
        try:
            doc = fetch_and_clean(url)
            text = doc.text
            title = doc.title
        except UnicodeDecodeError:
            raise
        except Exception, e:
            return HttpResponseServerError(str(e))

    elif uuid and not text:
        try:
            doc = get_object_or_404(SearchDocument, uuid=uuid)
            text = doc.text
            title = doc.title
        except UnicodeDecodeError:
            raise
        except Exception, e:
            return HttpResponseServerError(str(e))

    elif text:
        # Even if they are searching by text, create a document so it can
        # be recalled by uuid.
        doc = SearchDocument()
        doc.text = text
        doc.save()

    # The actual proxying:
    sfm = superfastmatch.DjangoClient()
    response = sfm.search(text, doctype)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        response['uuid'] = doc.uuid
        if (url or uuid) and text and 'text' not in response:
            response['text'] = text
        if title and 'title' not in response:
            response['title'] = title
        for row in response['documents']['rows']:
            row['fragments'] = reduce_fragments(row['fragments'])
        return HttpResponse(json.dumps(response, indent=2), content_type='application/json')

