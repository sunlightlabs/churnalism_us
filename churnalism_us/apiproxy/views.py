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
from apiproxy.models import SearchDocument, MatchedDocument, Match
from apiproxy.embellishments import calculate_coverage

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


def recall_document(title, url, uuid, text):
    doc = None

    if url:
        try:
            doc = SearchDocument.objects.lookup_by_url(url)
        except SearchDocument.DoesNotExist:
            pass

    elif text:
        doc = SearchDocument.objects.filter(text=text)
        if len(doc) > 0:
            doc = doc[0]

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
            try:
                #primitive match on exact text
                doc = SearchDocument.objects.filter(text__icontains=text)
                if len(doc) > 0:
                    doc = doc[0]
                else:
                    doc = SearchDocument()
            except:
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

        for r in response['documents']['rows']:
            try:
                md = MatchedDocument.objects.get(doc_id=r['docid'], doc_type=r['doctype'])
            except:
                md = MatchedDocument(doc_type=r['doctype'], 
                                    doc_id=r['docid'], 
                                    source_url=r['url'],
                                    source_name=r['docid'], #will change this later, for now just use the doc id
                                    source_headline=r['title'])
                md.save() 

            matches = Match.objects.filter(search_document=doc, matched_document=md)
            if len(matches) > 0:
                matches[0].number_matches += 1
                matches[0].save()
            else:
                stats = calculate_coverage(text, r)
                match = Match(search_document=doc, 
                              matched_document=md,
                              percent_sourced=0, #don't need this since churn function picks higher of sourced or churned
                              percent_churned=str(stats[1]),
                              number_matches=1)
                match.save()

        return HttpResponse(json.dumps(response, indent=2), content_type='application/json')













