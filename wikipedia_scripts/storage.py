# -*- coding: utf-8 -*-
"""
This module is intended to be used with the wikitools.pageprocessor
script. You can obtain a copy of the wikitools package here:

https://github.com/sunlightlabs/wikipedia-dump-tools
"""

from __future__ import division, print_function

import datetime
import lxml.etree

import leveldb
import superfastmatch

from django.conf import settings

__all__ = ['write_to_leveldb', 'add_to_superfastmatch']

PageDB = None
def write_to_leveldb(page_dom):
    global PageDB
    page_id = int(page_dom.find('id').text)
    if PageDB is None:
        PageDB = leveldb.LevelDB(u'pages_{now}.leveldb'.format(now=datetime.datetime.now().isoformat()))
    PageDB.Put(str(page_id), lxml.etree.tostring(page_dom))

sfm = superfastmatch.Client()
def add_to_superfastmatch(page_dom):
    revision_elem = page_dom.find('revision')
    params = {}
    params['doctype'] = getattr(settings, 'WIKIPEDIA_DOCTYPE', 10)
    params['docid'] = int(page_dom.find('id').text)
    params['title'] = page_dom.find('title').text
    # The url depends on transforms.add_url_attrib being called first
    # since transforms.append_month_to_title is also called.
    params['url'] = page_dom.attrib.get('url', '')
    # We want to preserve the leading and trailing line endings in the XML
    # but we drop them when adding them to superfastmatch.
    params['text'] = revision_elem.find('text').text.strip()
    params['source'] = 'Wikipedia'

    timestamp_elem = revision_elem.find('timestamp')
    timestamp = datetime.datetime.strptime(timestamp_elem.text, '%Y-%m-%dT%H:%M:%SZ')
    params['date'] = timestamp.strftime('%Y-%m-%d')

    doc = sfm.add(defer=True, **params)
    if u'error' in doc:
        print(u"Failed to POST document to SuperFastMatch server:", doc[u'error'])

