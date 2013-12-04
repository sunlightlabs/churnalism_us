# -*- coding: utf-8 -*-
"""
This module is intended to be used with the wikitools.pageprocessor
script. You can obtain a copy of the wikitools package here:

https://github.com/sunlightlabs/wikipedia-dump-tools
"""

from __future__ import division, print_function

import sys
import re
import math
import unicodecsv

from wikitools import DropPage

__all__ = []

ListItemPattern = re.compile(ur'^\s*\*', re.M)
LineEndingPattern = re.compile(ur'[\r\n]+')
def maximum_listitem_to_line_ratio(max_ratio, page_dom):
    elems = page_dom.xpath('/page/revision/text')
    if len(elems) > 0:
        text = elems[0].text
        if text is not None:
            text = text.strip()
            listitems = len(ListItemPattern.findall(text))
            lines = len(LineEndingPattern.split(text))
            if lines > 0:
                ratio = listitems / lines
                if ratio >= max_ratio:
                    raise DropPage(page_dom, u"listitem to line ratio too high: {li}/{ln} = {r} > {max}".format(li=listitems, ln=lines, r=ratio, max=max_ratio))
    return page_dom

csvout = None
def print_listitem_to_line_ratio(page_dom):
    global csvout
    doc_id = page_dom.find('id').text
    title = page_dom.find('title').text
    elems = page_dom.xpath('/page/revision/text')
    if len(elems) > 0:
        text = elems[0].text
        if text is not None:
            text = text.strip()
            listitems = len(ListItemPattern.findall(text))
            lines = len(LineEndingPattern.split(text))
            chars = len(text)
            if lines > 0:
                ratio = listitems / lines
                if csvout is None:
                    csvout = unicodecsv.writer(sys.stdout)
                    csvout.writerow([u'doc_id', u'listitems', u'lines', u'ratio', u'chars', u'title'])
                csvout.writerow([doc_id, listitems, lines, ratio, chars, title])

def print_document_line_stats(page_dom):
    global csvout
    doc_id = page_dom.find('id').text
    title = page_dom.find('title').text
    elems = page_dom.xpath('/page/revision/text')
    if len(elems) > 0:
        text = elems[0].text
        if text is not None:
            text = text.strip()
            listitems = len(ListItemPattern.findall(text))
            lines = LineEndingPattern.split(text)
            linecnt = len(lines)
            line_lengths = list(sorted([len(ln) for ln in lines]))
            chars = len(text)

            idx_n = len(lines) - 1
            if idx_n == -1:
                median = None
            elif idx_n == 0:
                median = line_lengths[0]
            elif idx_n == 1:
                median = sum(line_lengths) / 2
            elif idx_n % 2 == 0:
                median = line_lengths[int(idx_n / 2)]
            else:
                a = line_lengths[int(math.floor(idx_n / 2))]
                b = line_lengths[int(math.ceil(idx_n / 2))]
                median = (a + b) / 2

            if idx_n == -1:
                mean = None
            else:
                mean = sum(line_lengths) / len(line_lengths)

            if median is not None and mean is not None:
                if csvout is None:
                    csvout = unicodecsv.writer(sys.stdout)
                    csvout.writerow([u'doc_id',
                                     u'median', u'mean',
                                     u'lines', u'listitems',
                                     u'chars', u'title'])
                csvout.writerow([unicode(doc_id),
                                 unicode(median), unicode(mean),
                                 unicode(linecnt), unicode(listitems),
                                 unicode(chars), title])

def contains_convert_templates(page_dom):
    text = page_dom.find('revision').find('text').text
    if '{{convert' in text:
        return page_dom
    else:
        raise DropPage(page_dom, "Does not include {{convert")


