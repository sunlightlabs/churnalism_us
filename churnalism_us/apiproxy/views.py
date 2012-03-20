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


from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest, HttpResponseServerError)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import superfastmatch
from apiproxy.models import SearchDocument


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


def recall_document(title, url, uuid):
    doc = None

    if url:
        try:
            doc = SearchDocument.objects.lookup_by_url(url)
        except SearchDocument.DoesNotExist:
            pass

    if uuid and not doc:
        doc = get_object_or_404(SearchDocument, uuid=uuid)

    if not doc:
        raise SearchDocument.DoesNotExist()

    # If the extractor fails to extract a title, this will copy a title from
    # a later submission from an improved extractor.
    if title and not doc.title:
        doc.title = title
        doc.save()

    return doc


@csrf_exempt
def search(request, doctype=None):
    """
    Proxies /search/ to Superfastmatch, returning the response with 
    a few embellishments. If the text is given, it is stored in the
    database for later retrieval. It is assigned a UUID for later
    retrieval. This same view handles search via UUID recall.
    """

    text = request.POST.get('text') or request.GET.get('text')
    url = request.POST.get('url') or request.GET.get('url')
    uuid = request.POST.get('uuid') or request.GET.get('uuid')
    title = request.POST.get('title') or request.GET.get('title')
    doc = None

    if not text and not url and not uuid:
        return HttpResponseBadRequest()

    elif url or uuid:
        try:
            doc = recall_document(title, url, uuid)

            if not title:
                title = doc.title
            if not url:
                url = doc.url
            text = doc.text
        except UnicodeDecodeError:
            raise

        except SearchDocument.DoesNotExist:
            pass

        except Exception, e:
            return HttpResponseServerError(str(e))

    if not doc:
        if not text:
            return HttpResponseNotFound(str(url or uuid))
        else:
            doc = SearchDocument()
            doc.text = text
            doc.title = title
            if url:
                doc.url = url
            doc.save()

    # The actual proxying:
    sfm = superfastmatch.DjangoClient()
    response = sfm.search(text, doctype)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        response['uuid'] = doc.uuid
        if (url or uuid) and 'text' not in response:
            response['text'] = doc.text
        if title and 'title' not in response:
            response['title'] = doc.title
        return HttpResponse(json.dumps(response, indent=2), content_type='application/json')

