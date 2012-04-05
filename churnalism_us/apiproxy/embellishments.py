
from __future__ import division

from copy import deepcopy
from operator import itemgetter

import superfastmatch

def document_text(sfm, row):
    doc_result = sfm.document(row['doctype'], row['docid'])
    if doc_result['success'] == True:
        return doc_result['text']


def calculate_coverage(text, row):
    chars_matched = sum((fragment[2] for fragment in row['fragments']))
    pct_of_match = chars_matched / row['characters']
    pct_of_source = chars_matched / len(text)
    return [chars_matched, round(max(pct_of_match, pct_of_source) * 100, 2)]


def snippets_for_fragments(text, fragments):
    return list(set([text[frag[0]:frag[0]+frag[2]] for frag in fragments]))


def reduce_fragments(fragments):
    begin = itemgetter(0)
    origbegin = itemgetter(1)
    length = itemgetter(2)
    end = lambda f: begin(f) + length(f)

    def compare_bounds(a, b):
        if begin(a) == begin(b):
            return end(b) - end(a)
        else:
            return begin(a) - begin(b)

    def subsumes(a, b):
        return begin(a) <= begin(b) and end(b) <= end(a)

    def overlaps(a, b):
        if begin(a) <= begin(b) <= end(a):
            return True
        elif begin(b) <= begin(a) <= end(b):
            return True
        else:
            return False

    frags = deepcopy(fragments)
    frags.sort(cmp=compare_bounds)

    new_frags = []
    while len(frags) > 0:
        a = frags.pop(0)

        if len(frags) == 0:
            new_frags.append(a)
        else:
            while len(frags) > 0:
                b = frags.pop(0)
                if subsumes(a, b):
                    pass # Ignore b
                elif subsumes(b, a):
                    a = deepcopy(b)
                elif overlaps(a, b):
                    a = [min(begin(a), begin(b)),
                         min(origbegin(a), origbegin(b)),
                         max(end(a), end(b)),
                         None] # Neither hash applies
                else:
                    frags = [b] + frags
                    break
            new_frags.append(a)

    return new_frags


def embellish(text, sfm_results, reduce_frags=False, add_coverage=False, add_snippets=False, prefetch_documents=False):
    sfm = superfastmatch.DjangoClient()
    maxdocs = prefetch_documents if isinstance(prefetch_documents, int) else None
    prefetched = 0

    rows = iter(sfm_results['documents']['rows'])
    if prefetch_documents and maxdocs:
        rows = sorted(sfm_results['documents']['rows'], key=itemgetter('characters'))

    for row in rows:
        if reduce_frags:
            row['fragments'] = reduce_fragments(row['fragments'])

        if add_coverage:
            row['coverage'] = calculate_coverage(text, row)

        if add_snippets:
            row['snippets'] = snippets_for_fragments(text, row['fragments'])

        if prefetch_documents:
            if maxdocs is None or (maxdocs is not None and prefetched < maxdocs):
                row['text'] = document_text(sfm, row)

