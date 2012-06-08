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
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from utils.slurp_url import slurp_url

from apiproxy.models import SearchDocument, Match, MatchedDocument

import superfastmatch
from superfastmatch.djangoclient import from_django_conf
from utils.textextract import readability_extract

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
    sfm = from_django_conf('sidebyside')
    if maxdocs:
        results['documents']['rows'].sort(key=itemgetter('characters'))

    for (idx, row) in enumerate(results['documents']['rows']):
        if maxdocs and idx >= maxdocs:
            return

        doc_result = sfm.document(row['doctype'], row['docid'])
        if doc_result['success'] == True:
            row['text'] = doc_result['text']


def sort_by_coverage(results):
    def _compare(a, b):
        coverage_diff = a['coverage'][0] - b['coverage'][0]
        if coverage_diff == 0:
            density_diff = a['density'] - b['density']
            if density_diff == 0:
                return 0
            elif density_diff < 0:
                return -1
            else:
                return 1
        elif coverage_diff < 0:
            return -1
        else:
            return 1

    results['documents']['rows'].sort(cmp=_compare, reverse=True)

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
    sfm = from_django_conf('sidebyside')
    sfm_results = sfm.search(text)
    drop_silly_results(sfm_results)
    sort_by_coverage(sfm_results)
    return search_result_page(request, sfm_results, text)


def search_against_uuid(request, uuid):
    sfm = from_django_conf('sidebyside')
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
        elif settings.DEBUG == True:
            return HttpResponse(e.response[1], status=e.response[0])
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

        htmldoc = lxml.html.fromstring(html)
        to_remove = [e
                     for e in htmldoc.iterdescendants()
                     if e.tag == lxml.etree.Comment
                     or e.tag == 'script'
                     or e.tag == 'noscript'
                     or e.tag == 'object'
                     or e.tag == 'embed']
        for e in to_remove:
            e.getparent().remove(e)
        html = lxml.html.tostring(htmldoc)

        (title, text) = readability_extract(html)
        return (title, text)

    sfm = from_django_conf('sidebyside')
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
    sfm = from_django_conf('sidebyside')
    try:
        sfm_results = sfm.search(text=None, uuid=uuid)
        drop_silly_results(sfm_results)
        if len(sfm_results['documents']['rows']) == 0:
            return document404(request, uuid=uuid)

        sort_by_coverage(sfm_results)

        try:
            matching_row = [r 
                            for r in sfm_results['documents']['rows']
                            if r['doctype'] == int(doctype)
                            and r['docid'] == int(docid)][0]
        except IndexError:
            return redirect('sidebyside-uuid-search', uuid=uuid)

        if not matching_row.get('text'):
            doc = sfm.document(doctype, docid)
            if doc:
                matching_row['text'] = doc['text']

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

def recall(request, uuid, doctype, docid):
    sfm = from_django_conf('sidebyside')
    sfm_results = sfm.search(text=None, uuid=uuid)

    match_count = len(sfm_results['documents']['rows'])

    try:
        match = [r for r in sfm_results['documents']['rows']
                 if r['doctype'] == int(doctype)
                 and r['docid'] == int(docid)][0]
    except IndexError:
        return HttpResponseNotFound('Document {uuid} does not match document ({doctype}, {docid}).'.format(uuid=uuid, doctype=doctype, docid=docid))

    match_doc = sfm.document(match['doctype'], match['docid'])
    if match_doc['success'] == True:
        match_text = match_doc['text']
        match_title = match.get('title', '')
        match_url = match.get('url', '')
	match_source = match.get('source', '')
    sfm_results['documents']['rows'] = [match]

    if sfm_results.has_key('title'):
        title = sfm_results['title']
    else:
        title = '(No Title Found)'

    return {
        'results': sfm_results,
        'source_text': sfm_results['text'],
        'source_title': title,
        'source_url': sfm_results.get('url'),
        'uuid': uuid,
        'match_count': match_count, # Raw match count, unrelated to 'match' variables below
        'match': match,
        'match_text': match_text,
        'match_title': match_title,
        'match_url': match_url,
        'match_source': match_source }

def chromeext_parameters(request):
    minimum_pct = settings.SIDEBYSIDE.get('minimum_coverage_pct', 1)
    minimum_chars = settings.SIDEBYSIDE.get('minimum_coverage_chars', 180)
    results = {
        'minimum_coverage_pct': minimum_pct,
        'minimum_coverage_chars': minimum_chars,
        'warning_ribbon_src': reverse('sidebyside-chrome-ribbon')
    }
    return HttpResponse(json.dumps(results), content_type='application/json')

def chromeext_ribbon(request):
    scope = {
        'fake_domain': request.GET.get('domain')
    }
    return render(request, 'sidebyside/chrome_ribbon.html', scope)

def chromeext_recall(request, uuid, doctype, docid):
    scope = recall(request, uuid, doctype, docid)
    resp = render(request, 'sidebyside/chrome.html', scope)
    return resp

def generic_recall(request, uuid, doctype, docid):
    scope = recall(request, uuid, doctype, docid)
    resp = render(request, 'sidebyside/chrome.html', scope)
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
