# -*- coding: utf-8 -*-

import lxml.html
from operator import itemgetter
from lepl.apps.rfc3696 import HttpUrl
from django.shortcuts import render
from django.http import Http404

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


def search_page(request):
    return render(request, 'search_page.html', {})


def search_result_page(request, results, source_text, 
                       source_url=None, source_title=None):
    return render(request, 'search_result.html',
                  {'results': results,
                   'source_text': source_text,
                   'source_title': source_title,
                   'source_url': source_url})


def search(request, url=None):
    if request.method == 'GET':
        url = url or request.GET.get('url')
        if url not in ('', None):
            return search_against_url(request, url)

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
    attach_document_text(sfm_results, maxdocs=settings.SIDEBYSIDE.get('max_doc_prefetch'))
    return search_result_page(request, sfm_results, text)


def search_against_url(request, url):
    """
    Accepts a URL as either a suffix of the URI or a POST request 
    parameter. Downloads the content, feeds it through the
    readability article grabber, then submits the article text
    to superfastmatch for comparison.
    """

    sfm = superfastmatch.DjangoClient('sidebyside')
    sfm_results = sfm.search(text=None, url=url)
    attach_document_text(sfm_results, maxdocs=settings.SIDEBYSIDE.get('max_doc_prefetch'))
    return search_result_page(request, sfm_results, sfm_results['text'],
                              source_title=sfm_results['title'], source_url=url)


