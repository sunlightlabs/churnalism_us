# -*- coding: utf-8 -*-
from __future__ import division

import re
from copy import deepcopy


def freq(it):
    counts = {}
    for x in it:
        cnt = counts.get(x, 0)
        counts[x] = cnt + 1
    return counts


def drop_common_fragments(threshold, results):
    def _snippet(fragment):
        return results['text'][fragment[0]:][:fragment[2]]
    rows = results['documents']['rows']
    # We don't want to exclude a fragment that appears in just one or
    # two fragments simply because the results are too few to calculate
    # a percentage with sufficient fidelity.
    if 2 / len(rows) > threshold:
        return

    freqs = freq(frag[3] for row in rows for frag in row['fragments'])

    blacklist = [frag_hash
                 for (frag_hash, frag_freq) in freqs.items()
                 if frag_freq / len(rows) >= threshold]

    for row in rows:
        row['fragments'][:] = [
            fragment
            for fragment in row['fragments']
            if fragment[3] not in blacklist
        ]

    rows[:] = [row for row in rows if len(row['fragments']) > 0]


PrepositionPattern = re.compile(r'^(a|and|the|abaft|aboard|about|above|absent|across|afore|after|against|along|alongside|amid|amidst|among|amongst|an|apropos|around|as|aside|astride|at|athwart|atop|barring|before|behind|below|beneath|beside|besides|between|betwixt|beyond|but|by|circa|concerning|despite|down|during|except|excluding|failing|following|for|from|given|in|including|inside|into|lest|like|mid|midst|minus|modulo|near|next|notwithstanding|of|off|on|onto|opposite|out|outside|over|pace|past|per|plus|pro|qua|regarding|round|sans|save|since|than|through|throughout|till|times|to|toward|towards|under|underneath|unlike|until|unto|up|upon|versus|via|vice|with|within|without|worth|)$', re.IGNORECASE)
CapitalizedPattern = re.compile('^[A-Z].*')
TokenizingPattern = re.compile('[\s()]')

def proper_nouniness(s):
    def is_positive_signal(w):
        if CapitalizedPattern.match(w) is not None:
            return True
        elif PrepositionPattern.match(w) is not None:
            return True
        else:
            return False

    count = 0
    signal = 0
    words = TokenizingPattern.split(s)
    first_letter = s[0]
    if first_letter.islower() and PrepositionPattern.match(words[0]) is None:
        words = words[1:]

    for w in words:
        if w != '':
            if is_positive_signal(w):
                signal += 1
            count += 1

    if count == 0 or signal == 0:
        return 0
    else:
        return signal / count


def ignore_proper_nouns(threshold, text, results):
    def _snippet(fragment):
        return text[fragment[0]:][:fragment[2]]

    new_rows = []
    rows = results['documents']['rows']

    for row in rows:
        new_row = deepcopy(row)
        new_fragments = []

        for fragment in row['fragments']:
            snippet = _snippet(fragment)
            pnoun_score = proper_nouniness(snippet)
            if pnoun_score >= threshold:
                pass
                # print 'Dropping proper noun: {0}'.format(snippet)
            else:
                new_fragments.append(fragment)

        if len(new_fragments) > 0:
            new_row['fragments'] = new_fragments
            new_rows.append(new_row)

    results['documents']['rows'] = new_rows
