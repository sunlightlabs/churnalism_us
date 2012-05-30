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

from decimal import Decimal

from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest, HttpResponseServerError)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import superfastmatch
from apiproxy.models import SearchDocument, MatchedDocument, Match
from apiproxy.embellishments import calculate_coverage, embellish
from apiproxy.filters import drop_common_fragments, ignore_proper_nouns

from django.conf import settings


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
    order_by = request.GET.get('order_by')
    limit = request.GET.get('limit')
    response = sfm.documents(doctype, page=page, order_by=order_by, limit=limit)
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


def recall_document(title, url, uuid, text):
    doc = None

    if url:
        try:
            doc = SearchDocument.objects.lookup_by_url(url)
        except SearchDocument.DoesNotExist:
            pass

    if uuid and not doc:
        try:
            doc = SearchDocument.objects.get(uuid=uuid)
        except SearchDocument.DoesNotExist:
            pass

    if text and not doc:
        doc = SearchDocument.objects.filter(text=text)
        if len(doc) > 0:
            doc = doc[0]

    if not doc:
        raise SearchDocument.DoesNotExist()

    # If the extractor fails to extract a title, this will copy a title from
    # a later submission from an improved extractor.
    if title and not doc.title:
        doc.title = title
        doc.save()

    return doc


def stored_match(request, uuid):
    try:
        search_doc = SearchDocument.objects.get(uuid=uuid)
    except SearchDocument.DoesNotExist:
        return HttpResponseNotFound('{0} not found'.format(uuid))


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

    elif url or uuid or text:
        try:
            doc = recall_document(title, url, uuid, text)

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
            if title:
                doc.title = title
            if url:
                doc.url = url
            doc.save()


    # The actual proxying:
    response = execute_search(doc, doctype)
    record_matches(doc, response)

    # These changes are specific to this request and should not be stored in the database.
    response['uuid'] = doc.uuid
    if (url or uuid) and 'text' not in response:
        response['text'] = doc.text
    if title and 'title' not in response:
        response['title'] = doc.title

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')


def execute_search(doc, doctype=None):
    sfm = superfastmatch.DjangoClient()
    response = sfm.search(doc.text, doctype)

    if isinstance(response, str):
        # Pass the SFM error back to the client
        return HttpResponse(response, content_type='text/html')


    drop_common_fragments(settings.APIPROXY.get('commonality_threshold', 0.4), response)
    ignore_proper_nouns(settings.APIPROXY.get('proper_noun_threshold', 0.8),
                        doc.text, response)
    embellish(doc.text,
              response,
              **settings.APIPROXY.get('embellishments', {}))
    return response


def record_matches(doc, response, update_matches=False):
    sfm = superfastmatch.DjangoClient()
    for r in response['documents']['rows']:
        (md, created) = MatchedDocument.objects.get_or_create(doc_id=r['docid'],
                                                              doc_type=r['doctype'])
        if created or update_matches:
            sfm_doc = sfm.document(r['doctype'], r['docid'])
            if sfm_doc['success'] == False:
                # If we can't fetch the text, the site probably won't be able
                # to either, so just ignore this result row.
                continue
            md.text = sfm_doc['text']
            md.source_url = r['url']
            md.source_name = r['docid'] # This is wrong, should be the publisher
            md.source_headline = r['title']
            md.save()

        (match, created) = Match.objects.get_or_create(search_document=doc,
                                                       matched_document=md)
        if created or update_matches:
            stats = calculate_coverage(doc.text, r)
            match.percent_churned = str(stats[1])
            match.overlapping_characters = stats[0]
            density = r.get('density')
            match.fragment_density = Decimal(str(density)) if density else None
            match.response = json.dumps(response)
        match.number_matches += 1
        match.save()

        r['match_id'] = match.id







