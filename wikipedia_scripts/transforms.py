# -*- coding: utf-8 -*-
"""
This module is intended to be used with the wikitools.pageprocessor
script. You can obtain a copy of the wikitools package here:

https://github.com/sunlightlabs/wikipedia-dump-tools
"""

from __future__ import division, print_function

import re
import sys
import datetime
import urllib

from HTMLParser import HTMLParser

import lxml.etree
import inflect
words = inflect.engine()


__all__ = ['append_month_to_title', 'add_url_attrib']

MMMYYYY = datetime.date.today().strftime('%b, %Y')
TitleFmt = "{orig} ({mmmyyyy})"
def append_month_to_title(page_dom):
    title_elem = page_dom.find('title')
    if title_elem:
        title_elem.text = TitleFmt.format(orig=title_elem.text,
                                          mmmyyyy=MMMYYYY)
    return page_dom

def add_url_attrib(page_dom):
    title = page_dom.find('title').text
    title1 = title.replace(u' ', u'_')
    title2 = urllib.quote(title1.encode('utf-8'))
    title3 = title2.replace('%28', '(').replace('%29', ')')
    title4 = title3[0].upper() + title3[1:]
    url = u"https://en.wikipedia.org/wiki/{title}".format(title=title4)
    page_dom.attrib['url'] = url
    return page_dom


