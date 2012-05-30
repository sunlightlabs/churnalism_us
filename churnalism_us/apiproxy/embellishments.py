
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
    pct_of_combined = chars_matched / (row['characters'] + len(text) - chars_matched)
    return [chars_matched, round(pct_of_combined * 100, 2)]


def fragment_density(row):
    def _left(frag):
        return (frag[0], frag[2])
    def _right(frag):
        return (frag[1], frag[2])

    doc_extents = []
    for (side, _side) in [('searched', _left), ('matched', _right)]:
        if len(row['fragments']) == 1:
            doc_extents.append((0, row['characters'], row['fragments'][0][2]))
        else:
            # (min, max, sum)
            extents = (0xffffffff, 0, 0)
            for frag in row['fragments']:
                (start, length) = _side(frag)
                extents = (min(extents[0], start),
                           max(extents[1], start + length),
                           extents[2] + length)
            doc_extents.append(extents)
        # density[side] = extents[2] / (extents[1] - extents[0])

    (numer, denom) = reduce(lambda (numer, denom), (fro, to, l): (numer+l, denom+(to-fro)),
                            doc_extents, (0, 0))

    if denom == 0 or numer == 0:
        return 0
    else:
        return numer / denom


def snippets_for_fragments(text, fragments):
    return list(set([text[frag[0]:frag[0]+frag[2]] for frag in fragments]))


def eliminate_overlap(a, b):
    """
    Assuming a and b overlap, attributes the overlapping text to the 
    fragment with the shorter prefix/suffix.
    """

    begin = itemgetter(0)
    origbegin = itemgetter(1)
    length = itemgetter(2)
    end = lambda f: begin(f) + length(f)

    prelen = begin(b) - begin(a)
    postlen = end(b) - end(a)
    innerlen = end(a) - begin(b)

    if prelen > postlen:
        new_a = [begin(a),
                 origbegin(a),
                 prelen,
                 None]
        new_b = [begin(b),
                 origbegin(b),
                 innerlen + postlen,
                 None]

    else:
        new_a = [begin(a),
                 origbegin(a),
                 prelen + innerlen,
                 None]
        new_b = [end(a),
                 origbegin(b) + innerlen,
                 postlen,
                 None]

    return (new_a, new_b)


def reduce_fragments(fragments, minimum_threshold=15):
    """
    Eliminates fragment overlap.

    This function causes some right-side fragments to disappear. Therefore 
    fragments from this function cannot do right-side highlighting or snippeting 
    based on the reduced fragments.
    """

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
        if begin(a) <= begin(b) < end(a):
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
                    (a, b) = eliminate_overlap(a, b)
                    if length(a) <= minimum_threshold:
                        frags = [b] + frags
                        frags.sort(cmp=compare_bounds)
                        a = frags.pop(0)
                    elif length(b) <= minimum_threshold:
                        pass
                    else:
                        frags = [b] + frags
                        frags.sort(cmp=compare_bounds)
                        # Re-sort in case there is a fragment sequence like this:
                        # |      |
                        #     |       |
                        #      |        |

                else:
                    frags = [b] + frags
                    break
            new_frags.append(a)

    return new_frags


def embellish(text, sfm_results, reduce_frags=False, add_coverage=False, add_density=False, add_snippets=False, prefetch_documents=False):
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

        if add_density:
            row['density'] = fragment_density(row)

        if add_snippets:
            row['snippets'] = snippets_for_fragments(text, row['fragments'])

        if prefetch_documents:
            if maxdocs is None or (maxdocs is not None and prefetched < maxdocs):
                row['text'] = document_text(sfm, row)

