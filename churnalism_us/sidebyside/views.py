# -*- coding: utf-8 -*-

from __future__ import division

import json
import re
import httplib
import lxml.html
import readability
import settings
from operator import itemgetter
from urlparse import urlparse

import stream
from lepl.apps.rfc3696 import HttpUrl
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from apiproxy.embellishments import embellish
from utils.slurp_url import slurp_url

from apiproxy.models import SearchDocument, Match, MatchedDocument

import superfastmatch

from django.conf import settings



def ensure_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    url = 'http://' + url

    validator = HttpUrl()
    if validator(url) == True:
        return url
    
    raise ValueError('{url} is not a valid URL.'.format(url=url))


def render_text(el):
    """ like lxml.html text_content(), but with tactical use of whitespace for block elements """

    inline_tags = ( 'a', 'abbr', 'acronym', 'b', 'basefont', 'bdo', 'big',
        'br',
        'cite', 'code', 'dfn', 'em', 'font', 'i', 'img', 'input',
        'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span',
        'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var',
        'applet', 'button', 'del', 'iframe', 'ins', 'map', 'object',
        'script' )

    txt = u''
    if isinstance(el, lxml.html.HtmlComment):
        return txt

    tag = str(el.tag).lower()
    if tag not in inline_tags:
        txt += u"\n";

    if el.text is not None:
        txt += unicode(el.text)
    for child in el.iterchildren():
        txt += render_text(child)
        if child.tail is not None:
            txt += unicode(child.tail)

    if el.tag=='br' or tag not in inline_tags:
        txt += u"\n";

    txt = re.sub(r'[\r\n]{2,}', '\n\n', txt)
    txt = re.sub(r'[\r\n]\s+[\r\n]', '\n\n', txt)

    return txt


def attach_document_text(results, maxdocs=None):
    sfm = superfastmatch.DjangoClient('sidebyside')
    if maxdocs:
        results['documents']['rows'].sort(key=itemgetter('characters'))

    for (idx, row) in enumerate(results['documents']['rows']):
        if maxdocs and idx >= maxdocs:
            return

        doc_result = sfm.document(row['doctype'], row['docid'])
        if doc_result['success'] == True:
            row['text'] = doc_result['text']


def sort_by_coverage(results):
    results['documents']['rows'].sort(key=lambda r: r['coverage'][1], reverse=True)


def drop_silly_results(results):
    minimum_pct = settings.SIDEBYSIDE.get('minimum_coverage_pct', 1)
    minimum_chars = settings.SIDEBYSIDE.get('minimum_coverage_chars', 180)
    results['documents']['rows'][:] = [
        row
        for row in results['documents']['rows']
        if round(row['coverage'][1]) >= minimum_pct
        and row['coverage'][0] >= minimum_chars
    ]


def search_page(request, error=None):
    context = {
        'brokenurl': request.GET.get('brokenurl') == 'true',
        'error': error
    }

    return render(request, 'sidebyside/search_page.html', context)


def search_result_page(request, results, source_text, 
                       source_url=None, source_title=None):
 #   embellish(source_text, 
 #             results, 
 #             reduce_frags=True,
 #             add_coverage=True, 
 #             add_snippets=True,
 #             prefetch_documents=settings.SIDEBYSIDE.get('max_doc_prefetch'))
    return render(request, 'sidebyside/search_result.html',
                  {'results': results,
                   'source_text': source_text,
                   'source_title': source_title,
                   'source_url': source_url,
                   'domain': settings.DOMAIN})


def search(request, url=None, uuid=None):
    if request.method == 'GET':
        url = url or request.GET.get('url')
        if url not in ('', None):
            return search_against_url(request, url)

        uuid = uuid or request.GET.get('uuid')
        if uuid not in ('', None):
            return search_against_uuid(request, uuid)

    elif request.method == 'POST':
        url = request.POST.get('url')
        if url not in ('', None):
            return search_against_url(request, url)

        text = request.POST.get('text')
        if text not in ('', None):
            return search_against_text(request, text)

    raise Http404()


def search_against_text(request, text):
    sfm = superfastmatch.DjangoClient('sidebyside')
    sfm_results = sfm.search(text)
    drop_silly_results(sfm_results)
    sort_by_coverage(sfm_results)
    return search_result_page(request, sfm_results, text)


def search_against_uuid(request, uuid):
    sfm = superfastmatch.DjangoClient('sidebyside')
    try:
        sfm_results = sfm.search(text=None, uuid=uuid)
        drop_silly_results(sfm_results)
        sort_by_coverage(sfm_results)
        return search_result_page(request, sfm_results, 
                                  source_text=sfm_results.get('text'), 
                                  source_title=sfm_results.get('title'))
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            return document404(request, uuid=uuid)
        else:
            raise


def search_against_url(request, url):
    """
    Accepts a URL as either a suffix of the URI or a POST request 
    parameter. Downloads the content, feeds it through the
    readability article grabber, then submits the article text
    to superfastmatch for comparison.
    """

    (scheme, _1, _2, _3, _4, _5) = urlparse(url)
    if scheme not in ('http', 'https'):
        return search_page(request, error='The URL must begin with either http or https.')

    def fetch_and_clean(url):
        html = slurp_url(url, use_cache=True)
        if not html:
            raise Exception('Failed to fetch {0}'.format(url))

        doc = readability.Document(html)
        cleaned_html = doc.summary()
        content_dom = lxml.html.fromstring(cleaned_html)
        try:
            title = doc.short_title()
        except: 
            title = 'No Title'
        return (title, render_text(content_dom).strip().encode('utf-8', 'replace').decode('utf-8'))

    sfm = superfastmatch.DjangoClient('sidebyside')
    (title, text) = fetch_and_clean(url)
    try:
        sfm_results = sfm.search(text=text, title=title, url=url)
        drop_silly_results(sfm_results)
        sort_by_coverage(sfm_results)


        #if they submit a url, don't return the exact same url in the results
        for r in sfm_results['documents']['rows']:
            if r['url'] == url:
                sfm_results['documents']['rows'].remove(r)
    
        if sfm_results.has_key('text'): text = sfm_results['text']
        else: text = ''

        if sfm_results.has_key('title'): title = sfm_results['title']
        else: title='No Title'

        return search_result_page(request, sfm_results, text,
                                  source_title=title, source_url=url)
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            return document404(request, url=url)
        elif settings.DEBUG == True:
            return HttpResponse(e.response[1], status=e.response[0])
        else:
            raise


def permalink(request, uuid, doctype, docid):
    sfm = superfastmatch.DjangoClient('sidebyside')
    try:
        sfm_results = sfm.search(text=None, uuid=uuid)
        drop_silly_results(sfm_results)
        sort_by_coverage(sfm_results)

        for row in sfm_results['documents']['rows']:
            if row['doctype'] == doctype and row['docid'] == docid:
                if not row.get('text'):
                    doc = sfm.document(doctype, docid)
                    if doc:
                        row['text'] = doc['text']

        return search_result_page(request, sfm_results,
                                  source_text=sfm_results['text'],
                                  source_title=sfm_results.get('title'),
                                  source_url=sfm_results.get('url'))
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            return document404(request, uuid=uuid)
        else:
            raise


def document404(request, uuid=None, url=None):
    return render(request, 'documentmissing.html',
                  {'uuid': uuid,
                   'url': url
                  })

def select_best_match(text, sfm_results):
    rows = sfm_results['documents']['rows']

    def fragment_match_percentage(row):
        chars_matched = sum((frag[2] for frag in row['fragments']))
        pct_of_match = float(chars_matched) / float(row['characters'])
        pct_of_source = float(chars_matched) / float(len(text))
        return (row, max(pct_of_match, pct_of_source))

    def longer(a, b):
        (row_a, pct_a) = a
        (row_b, pct_b) = b
        return a if pct_a >= pct_b else b

    return (stream.Stream(rows)
            >> stream.map(fragment_match_percentage)
            >> stream.reduce(longer, (None, 0)))

def chromeext_recall(request, uuid, doctype, docid):
    sfm = superfastmatch.DjangoClient('sidebyside')
    sfm_results = sfm.search(text=None, uuid=uuid)

    match_count = len(sfm_results['documents']['rows'])

    try:
        match = [r for r in sfm_results['documents']['rows']
                 if r['doctype'] == int(doctype)
                 and r['docid'] == int(docid)][0]
    except IndexError:
        return HttpResponseNotFound('Document {uuid} does not match document ({doctype}, {docid}).'.format(uuid=uuid, **match))

    match_doc = sfm.document(match['doctype'], match['docid'])
    if match_doc['success'] == True:
        match_text = match_doc['text']
        match_title = match.get('title', '')
        match_url = match.get('url', '')
	match_source = match.get('source', '')
    sfm_results['documents']['rows'] = [match]
    embellish(sfm_results['text'], sfm_results, add_snippets=True, add_coverage=True)

    if sfm_results.has_key('title'):
        title = sfm_results['title']
    else:
        title = '(No Title Found)'

    resp = render(request, 'sidebyside/chrome.html',
                  {'results': sfm_results,
                   'source_text': sfm_results['text'],
                   'source_title': title,
                   'source_url': sfm_results.get('url'),
                   'uuid': uuid,
                   'match_count': match_count, # Raw match count, unrelated to 'match' variables below
                   'match': match,
                   'match_text': match_text,
                   'match_title': match_title,
                   'match_url': match_url,
                   'match_source': match_source })
    return resp

def sidebyside_generic(request, search_uuid, match_doc_type, match_doc_id):

    search_doc = SearchDocument.objects.get(uuid=search_uuid)
    match_doc = MatchedDocument.objects.filter(doc_type=match_doc_type, doc_id=match_doc_id)[0]
    match = Match.objects.get(search_document=search_doc, matched_document=match_doc)

    # Prune other documents from the original response 
    cached_response = json.loads(match.response)
    cached_response['documents']['rows'] = [r for r in cached_response['documents']['rows'] 
                                            if r['doctype'] == int(match_doc_type) and r['docid'] == int(match_doc_id)]

    resp = render(request, 'sidebyside/chrome.html',
                            {'source_text': search_doc.text,
                             'source_title': search_doc.title,
                             'match_text': match_doc.text,
                             'match_title': match_doc.source_headline,
                             'match_source': match_doc.source_name,
                             'match': {'coverage': [None, match.percent_churned],
                                       'doctype': match_doc.doc_type,
                                       'docid': match_doc.doc_id
                                      },
                             'match_obj': match_doc,
                             'uuid': search_uuid,
                             'results': cached_response })
    return resp

def shared(request, uuid):
    """ Mark a SearchDocument as shared -- for analytics and footer modules """
    
    try:
        doc = SearchDocument.objects.get(uuid=uuid)
        if doc.times_shared: 
            doc.times_shared += 1
        else:
            doc.times_shared = 1
        doc.save()
        return HttpResponse("OK", content_type="text/html")
    except:
        return HttpResponseServerError()

def confirmed(request, match_id):
    try:
        match = Match.objects.get(id=match_id)
        if match.confirmed:
            match.confirmed += 1
        else:
            match.confirmed = 1
        match.save()
        return HttpResponse("OK", content_type="text/html")
    except:
        return HttpResponseServerError()

def urlproblem(request):
    url = request.GET.get('brokenurl', '')
    f = open(settings.PROJECT_ROOT + '/logs/broken_urls.log', 'a') 
    f.write(url)
    return HttpResponse("OK", content_type="text/html")
