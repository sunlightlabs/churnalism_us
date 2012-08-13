# -*- coding: utf-8 -*-

from __future__ import division

import json
import re
import httplib
import hashlib
import lxml.html
import lxml.etree
import settings
from operator import itemgetter
from urlparse import urlparse
from django.core.mail import send_mail
from lepl.apps.rfc3696 import HttpUrl
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from utils.fetch_and_clean import fetch_and_clean

from apiproxy.models import SearchDocument, Match, MatchedDocument, IncorrectTextReport

import superfastmatch
from superfastmatch.djangoclient import from_django_conf

from django.conf import settings


def contact_submission(request):
    params = request.POST
    if params.has_key('email') and params.has_key('text') and params.has_key('name'):
        #has required params
        
        send_mail('Contact from %s at %s' % (params['name'], params['email']), params['text'], 'contact@sunlightfoundation.com', settings.ADMIN_EMAILS)
       
        return HttpResponse('OK', content_type="text/plain")
        
    else:
        raise HttpResponseNotFound


def ensure_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    url = 'http://' + url

    validator = HttpUrl()
    if validator(url) == True:
        return url
    
    raise ValueError('{url} is not a valid URL.'.format(url=url))


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

    if settings.SIDEBYSIDE.get('allow_search') == True:
        context['allow_search'] = True

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
            raise Http404('No such article {0}'.format(uuid))
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

    sfm = from_django_conf('sidebyside')
    (title, text) = fetch_and_clean(url)
    try:
        sfm_results = sfm.search(text=text, title=title, url=url)
        drop_silly_results(sfm_results)
        sort_by_coverage(sfm_results)


        #if they submit a url, don't return the exact same url in the results
        for r in sfm_results['documents']['rows']:
            if r.get('url') == url:
                sfm_results['documents']['rows'].remove(r)
    
        if sfm_results.has_key('text'): text = sfm_results['text']
        else: text = ''

        if sfm_results.has_key('title'): title = sfm_results['title']
        else: title='No Title'

        return search_result_page(request, sfm_results, text,
                                  source_title=title, source_url=url)
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            raise HttpResponse('No such article {0}'.format(url))
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
            raise Http404('No such article {0}'.format(uuid))

        sort_by_coverage(sfm_results)

        try:
            matching_row = [r 
                            for r in sfm_results['documents']['rows']
                            if r['doctype'] == int(doctype)
                            and r['docid'] == int(docid)][0]
        except IndexError:
            return redirect('sidebyside-uuid-search', uuid=uuid)

        if not matching_row.get('text'):
            try:
                md = MatchedDocument.objects.get(doc_type=doctype, doc_id=docid)
                matching_row['text'] = md.text
            except MatchedDocument.DoesNotExist:
                doc = sfm.document(doctype, docid)
                if doc:
                    matching_row['text'] = doc['text']

        return search_result_page(request, sfm_results,
                                  source_text=sfm_results['text'],
                                  source_title=sfm_results.get('title'),
                                  source_url=sfm_results.get('url'))
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            raise Http404('No such article {0}'.format(uuid))
        else:
            raise

def recall(request, uuid, doctype, docid):
    sfm = from_django_conf('sidebyside')
    try:
        sfm_results = sfm.search(text=None, uuid=uuid)
    except superfastmatch.SuperFastMatchError, e:
        if e.status == httplib.NOT_FOUND:
            raise Http404('Article {uuid} not found'.format(uuid=uuid))
        else:
            raise

    match_count = len(sfm_results['documents']['rows'])

    try:
        match = [r for r in sfm_results['documents']['rows']
                 if r['doctype'] == int(doctype)
                 and r['docid'] == int(docid)][0]
        sfm_results['documents']['rows'] = [match]
    except IndexError:
        raise Http404('Article {uuid} does not match document ({doctype}, {docid}).'.format(uuid=uuid, doctype=doctype, docid=docid))

    match_doc = sfm.document(match['doctype'], match['docid'])
    if match_doc['success'] == False:
        raise Http404('Unable to retrieve document ({doctype}, {docid}).'.format(doctype=doctype, docid=docid))

    match_text = match_doc['text']
    match_title = match.get('title') or match_doc.get('title') or ''
    match_url = match.get('url') or match_doc.get('url') or ''
    match_source = match.get('source') or match_doc.get('source') or ''

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

def ie8ext_ribbon(request):
    scope = {
        'fake_domain': request.GET.get('domain'),
        'doctype': request.GET.get('doctype'),
        'docid': request.GET.get('docid'),
        'uuid': request.GET.get('uuid')
    }
    return render(request, 'sidebyside/ie8_ribbon.html', scope)


def chromeext_ribbon(request):
    scope = {
        'fake_domain': request.GET.get('domain')
    }
    return render(request, 'sidebyside/chrome_ribbon.html', scope)

def chromeext_recall(request, uuid, doctype, docid):
    scope = recall(request, uuid, doctype, docid)
    resp = render(request, 'sidebyside/chrome.html', scope)
    return resp

def ffext_parameters(request):
    return chromeext_parameters(request)

def ffext_ribbon(request):
    return chromeext_ribbon(request)

def ffext_recall(request, uuid, doctype, docid):
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


class ProblemReportForm(forms.Form):
    problem_description = forms.CharField(max_length=10000, widget=forms.Textarea)


def get_or_create_problem_report(request, search_document, remote_addr_hash):
    (report, created) = IncorrectTextReport.objects.get_or_create(search_document=search_document, remote_addr=remote_addr_hash)
    if created:
        report.user_agent = request.META.get('HTTP_USER_AGENT')
        report.languages = request.META.get('HTTP_ACCEPT_LANGUAGE')
        report.encodings = request.META.get('HTTP_ACCEPT_ENCODING')
        report.save()
    return report

def describe_text_problem(request, uuid):
    search_document = get_object_or_404(SearchDocument, uuid=uuid)
    remote_addr = request.META.get('REMOTE_ADDR')
    if not remote_addr:
        return render(request, 'sidebyside/text_problem.html', {'report': None})

    remote_addr_hash = hashlib.sha1(remote_addr).hexdigest()
    report = get_or_create_problem_report(request, search_document, remote_addr_hash)
    scope = {
        'uuid': uuid,
        'search_document': search_document,
        'report': report
    }

    if request.method == 'POST':
        form = ProblemReportForm(request.POST)
        if form.is_valid():
            report.problem_description = form.cleaned_data['problem_description']
            report.save()
            scope['form'] = None
        else:
            scope['form'] = form
    else:
        scope['form'] = ProblemReportForm()

    return render(request, 'sidebyside/text_problem.html', scope)

