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


from __future__ import division


import json
import socket
import math
import urllib
import datetime
import logging
from copy import deepcopy

from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest, HttpResponseServerError,
                         Http404)
from django.shortcuts import get_object_or_404

import superfastmatch
from superfastmatch.djangoclient import from_django_conf
from apiproxy.models import SearchDocument, MatchedDocument, Match
from apiproxy.embellishments import calculate_coverage, embellish
from apiproxy.filters import drop_common_fragments, ignore_proper_nouns
from utils.fetch_and_clean import fetch_and_clean

from django.conf import settings



from functools import wraps
def sfm_proxy_view(viewfunc):
    @wraps(viewfunc)
    def handled(request, *args, **kwargs):
        try:
            return viewfunc(request, *args, **kwargs)
        except socket.error as err:
            return HttpResponse(content='<html><h1>502 Bad Gateway</h1></html>',
                                status=502)
        except superfastmatch.SuperFastMatchError as err:
            return HttpResponse(content='<html><h1>502 Bad Gateway</h1></html>',
                                status=502)
    return handled

def timed(viewfunc):
    @wraps(viewfunc)
    def handled(*args, **kwargs):
        t1 = datetime.datetime.now()
        r = viewfunc(*args, **kwargs)
        t2 = datetime.datetime.now()
        dur = t2 - t1
        logging.debug("{0} call took {1} seconds".format(viewfunc.__name__, dur.total_seconds()))
        return r
    return handled

@sfm_proxy_view
def association(request, doctype=None):
    """
    Proxies requests for lists of associations to Superfastmatch.
    """

    sfm = from_django_conf()
    page = request.GET.get('cursor')
    response = sfm.associations(doctype, page)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


@sfm_proxy_view
@cache_page(60 * 5)
def document_list(request, doctype=None):
    """
    Proxies requests for lists of documents to Superfastmatch.
    """

    sfm = from_django_conf()
    page = request.GET.get('cursor')
    order_by = request.GET.get('order_by', 'docid')
    limit = request.GET.get('limit', '100')
    response = sfm.documents(doctype, page=page, order_by=order_by, limit=limit)
    if isinstance(response, str):
        return HttpResponse(response, content_type='text/html')
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


@csrf_exempt
@sfm_proxy_view
def document(request, doctype, docid):
    """
    Proxies requests for specific documents to Superfastmatch.
    """

    sfm = from_django_conf()
    if request.method == 'POST':
        params = request.POST
        if params['put'] == 'False':
            response = sfm.add(doctype, docid, params["text"], False, title=params['title'], date=params['date'], source=params['source'])
        else: 
            response = sfm.add(doctype, docid, params["text"], True, title=params['title'], date=params['date'], source=params['source'])

    else:
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


@sfm_proxy_view
#@cache_page(60 * 5)
def uuid_search(request, uuid, doctype=None):
    doc = get_object_or_404(SearchDocument, uuid=uuid)

    response = execute_search(doc, doctype)
    if isinstance(response, HttpResponse):
        return response

    record_matches(doc, response)

    # These changes are specific to this request and should not be stored in the database.
    response['uuid'] = doc.uuid
    response['text'] = doc.text
    response['title'] = doc.title
    response['url'] = doc.url

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')


def fetch_and_store(url):
    try:
        (title, text) = fetch_and_clean(url)
    except Exception:
        raise Http404(url)

    doc = SearchDocument()
    doc.url = url
    doc.title = title
    doc.text = text
    doc.save()
    return doc


@sfm_proxy_view
def url_search(request, doctype):
    url = request.GET.get('url')
    if not url:
        return HttpResponseNotFound(url)
    try:
        doc = SearchDocument.objects.get(url=url)
    except SearchDocument.DoesNotExist:
        doc = fetch_and_store(url)

    response = execute_search(doc, doctype)
    if isinstance(response, HttpResponse):
        return response

    record_matches(doc, response)

    response['uuid'] = doc.uuid
    response['text'] = doc.text
    response['title'] = doc.title
    response['url'] = doc.url

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')


@csrf_exempt
@sfm_proxy_view
@cache_page(60 * 5)
def search(request, doctype=None):
    """
    Proxies /search/ to Superfastmatch, returning the response with 
    a few embellishments. If the text is given, it is stored in the
    database for later retrieval. It is assigned a UUID for later
    retrieval. This same view handles search via UUID recall.
    """

    if request.method == 'GET':
        uuid = request.GET.get('uuid')
        url = request.GET.get('url')
        if uuid:
            return uuid_search(request, uuid, doctype)
        elif url:
            return url_search(request, doctype)
        else:
            return HttpResponseBadRequest('GET request with no URL or UUID')

    if request.method != 'POST':
        return HttpResponseBadRequest('Only GET and POST search requests allowed.')

    text = request.POST.get('text')
    url = request.POST.get('url')
    uuid = request.POST.get('uuid')
    title = request.POST.get('title')
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
            print text
            doc.text = text
            if title:
                doc.title = title
            if url:
                doc.url = url
            ua_string = request.META.get('HTTP_USER_AGENT')
            if ua_string is not None:
                doc.user_agent = ua_string[:255]
            doc.save()


    # The actual proxying:
    response = execute_search(doc, doctype)
    if isinstance(response, HttpResponse):
        return response

    record_matches(doc, response)

    # These changes are specific to this request and should not be stored in the database.
    response['uuid'] = doc.uuid
    if (url or uuid) and 'text' not in response:
        response['text'] = doc.text
    if title and 'title' not in response:
        response['title'] = doc.title
    if uuid and doc.url:
        response['url'] = doc.url

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')


def execute_search(doc, doctype=None):
    sfm = from_django_conf()
    response = sfm.search(doc.text, doctype)

    if isinstance(response, str):
        # Pass the SFM error back to the client
        return HttpResponse(response, content_type='text/html')


    drop_common_fragments(settings.APIPROXY.get('commonality_threshold', 0.4), response)

    ignore_proper_nouns(settings.APIPROXY.get('proper_noun_threshold', 0.8),
                        doc.text, response)

    if doc.url:
        response['documents']['rows'][:] = [r for r in response['documents']['rows']
    
                                            if r.get('url') != doc.url]
    embellish(doc.text,
                response,
                **settings.APIPROXY.get('embellishments', {}))
    return response


def record_matches(doc, response, update_matches=False):
    sfm = from_django_conf()
    for r in response['documents']['rows']:
        if 'url' not in r:
            # We don't want to record a match for a document we don't have a URL for
            # because we cannot provide a link back to the original.
            continue

        if r['url'] == doc.url:
            continue

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
            md.source_name = r.get('source')
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


# Mimicked variations of the API end points. All results here come
# from the database. These endpoints can be used for redundancy in
# the case  that the superfastmatch server is unreachable or unresponsive.

class DocumentProxy(object):
    field_mapping = {
        'docid': 'doc_id',
        'doctype': 'doc_type',
        'url': 'source_url',
        'title': 'source_headline',
        'source': 'source_name'
    }

    def __init__(self, real):
        self.real = real

    def __getitem__(self, item):
        if item == 'characters':
            return len(self.real.text)
        elif item == 'date':
            # TODO: MatchedDocument doesn't store the actual date. Make
            # it do so and then update this.
            return self.real.created.strftime('%Y-%m-%d')
        else:
            return getattr(self.real, self.translate_field(item))

    def __iter__(self):
        return iter(DocumentProxy.keys())

    @staticmethod
    def translate_field(attr):
        return DocumentProxy.field_mapping.get(attr, attr)

    @staticmethod
    def keys():
        return DocumentProxy.field_mapping.keys() + ['date', 'characters', 'text']

    @staticmethod
    def meta_fields():
        return DocumentProxy.field_mapping.keys() + ['date', 'characters']

def failure_response(msg):
    failure = {
        'success': False,
        'error': msg if settings.DEBUG else 'Generic, unhelpful error.'
    }
    return HttpResponse(json.dumps(failure), content_type='application/json')


def mimicked_document(request, doctype, docid):
    try:
        return real_mimicked_document(request, doctype, docid)
    except Exception, e:
        return failure_response(repr(e))


def real_mimicked_document(request, doctype, docid):
    doctype = int(doctype)
    docid = int(docid)

    matched_doc = MatchedDocument.objects.get(doc_type=doctype, doc_id=docid)
    proxied_doc = DocumentProxy(matched_doc)
    result = {
        'success': True,
    }
    result.update(proxied_doc)

    return HttpResponse(json.dumps(result), content_type='application/json')


def cursor_from_queryset(queryset, order_by_field, offset):
    try:
        doc = queryset[offset:][0]
        return '{metavalue}:{doctype}:{docid}'.format(
            metavalue=urllib.quote(getattr(doc, order_by_field)),
            doctype=doc.doc_type,
            docid=doc.doc_id)
    except IndexError:
        return ''


def mimicked_document_list(request, doctype=None):
    try:
        return real_mimicked_document_list(request, doctype)
    except Exception, e:
        return failure_response(repr(e))


def real_mimicked_document_list(request, doctype):
    """
    Mimics requests for lists of documents to Superfastmatch.
    """

    cursor = request.GET.get('cursor')
    limit = int(request.GET.get('limit', '100'))
    order_by = request.GET.get('order_by', 'docid')

    order_by_field = DocumentProxy.translate_field(order_by.lstrip('-'))
    order_by_direction = '-' if order_by.startswith('-') else ''
    filter_comparison = 'lte' if order_by_direction == '-' else 'gte'

    query = MatchedDocument.objects.all()

    if doctype:
        query = query.filter(doc_type=doctype)
    document_count = query.count()

    last_cursor = cursor_from_queryset(query, order_by_field,
                                       math.floor(document_count / limit) * limit)

    if order_by:
        query = query.order_by(order_by_direction + order_by_field).order_by(order_by_direction + 'doc_type').order_by(order_by_direction + 'doc_id')

    previous_cursor = ''
    previous_query = deepcopy(query)

    if cursor:
        filter_args = {}
        (curval, doctype, docid) = cursor.split(':')
        if order_by:

            filter_key = '{field}__{comp}'.format(field=order_by_field, comp=filter_comparison)
            filter_args[filter_key] = curval

            doctype_filter_key = 'doc_type__{comp}'.format(comp=filter_comparison)
            filter_args[doctype_filter_key] = doctype

            docid_filter_key = 'doc_id__{comp}'.format(comp=filter_comparison)
            filter_args[docid_filter_key] = docid

            query = query.filter(**filter_args)

            remainder_count = query.count()
            current_offset = document_count - remainder_count
            current_page = math.floor(current_offset / limit)
            previous_offset = max(0, (current_page - 1) * limit)
            previous_cursor = cursor_from_queryset(previous_query, order_by_field,
                                                   previous_offset)


    next_cursor = cursor_from_queryset(query, order_by_field, limit)

    results_query = query[:limit]

    current_cursor = cursor_from_queryset(results_query, order_by_field, 0)

    rows = [
        {'doctype': document.doc_type,
         'docid': document.doc_id,
         'title': document.source_headline,
         'url': document.source_url,
         'source': document.source_name,
         'characters': len(document.text),
         'date': document.created.strftime('%Y-%m-%d')
        }
        for document in results_query
    ]
    response = {}
    response['success'] = True
    response['metaData'] = {
        'fields': DocumentProxy.meta_fields()
    }
    response['cursors'] = {
        'next': next_cursor,
        'last': last_cursor,
        'previous': '' if previous_cursor == current_cursor else previous_cursor,
        'first': '',
        'current': current_cursor
    }
    response['total'] = document_count
    response['rows'] = rows

    return HttpResponse(json.dumps(response), content_type='application/json')


def stored_results(doc):
    matches = list(Match.objects.filter(search_document=doc))
    if len(matches) == 0:
        return []

    old_response = json.loads(matches[0].response)
    for r in old_response['documents']['rows']:
        if 'match_id' in r:
            del r['match_id']

    return old_response['documents']['rows']


@csrf_exempt
def mimicked_search(request, doctype=None):
    try:
        return real_mimicked_search(request, doctype)
    except Exception, e:
        return failure_response(repr(e))


def real_mimicked_search(request, doctype):
    text = request.POST.get('text') or request.GET.get('text')
    url = request.POST.get('url') or request.GET.get('url')
    uuid = request.POST.get('uuid') or request.GET.get('uuid')
    title = request.POST.get('title') or request.GET.get('title')
    doc = None

    if not text and not url and not uuid:
        return HttpResponseBadRequest('You must specify a url, a uuid, or some text')

    result = {
        'success': True,
        'metaData': {
            'fields': DocumentProxy.meta_fields()
        }
    }
    if url or uuid:
        try:
            doc = recall_document(title, url, uuid, text)
            result['uuid'] = doc.uuid
            result['title'] = doc.title
            result['text'] = doc.text
            result['documents'] = {
                'rows': stored_results(doc)
            }

        except SearchDocument.DoesNotExist:
            return HttpResponseNotFound(str(uuid or url))

    else:
        # TODO: Search by text
        return HttpResponseNotFound('Not yet implemented.')

    return HttpResponse(json.dumps(result), content_type='application/json')

