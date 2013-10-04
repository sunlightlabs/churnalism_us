# -*- coding: utf-8 -*-

"""
The underlying cause of the MatchedDocument models missing text is unknown.
Until we find the underlying cause, there is a significant chance that this
command is useless.
"""

from __future__ import division, print_function

import sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

import unicodecsv

import superfastmatch

from apiproxy.models import MatchedDocument
from utils.batched_results import batched_results

class Command(BaseCommand):
    help = 'Finds documents in the database that are missing text. Prints a CSV listing to stdout. Optionally attempts to fix them.'
    option_list = BaseCommand.option_list + (
        make_option('--autofix',
                    action='store_true',
                    dest='autofix',
                    default=False,
                    help='Whether to attempt to fix the document by fetching the text from the Superfastmatch server.'),
        make_option('--document',
                    action='store',
                    dest='document',
                    default=None,
                    help='doctype and docid of a specific document to fix e.g. 10,41202')
    )

    def handle(self, *args, **options):
        doctype = None
        docid = None
        if options['document'] is not None:
            try:
                (doctype, docid) = options['document'].split(',')
                doctype = int(doctype)
                docid = int(docid)
            except ValueError:
                raise CommandError(u"You must specify a doctype and docid separated by a comma for the --document option.")

        wrtr = unicodecsv.writer(sys.stdout, encoding='utf-8')

        if options['autofix'] == True:
            sfm = superfastmatch.from_django_conf('sidebyside')

        if doctype is None and docid is None:
            query = MatchedDocument.objects.filter(Q(text__isnull=True) | Q(text=''))
            cnt = query.count()
            if cnt == 0:
                raise CommandError(u"No MatchedDocuments are missing text.")
            docs = batched_results(query, batch_size=1000)

        else:
            docs = list(MatchedDocument.objects.filter(doc_type=doctype, doc_id=docid))
            if len(docs) == 0:
                raise CommandError(u"No such MatchedDocument: ({},{})".format(doctype, docid))
            elif len(docs[0].text.strip()) > 0:
                raise CommandError(u"MatchedDocument ({},{}) already has non-empty text.".format(doctype, docid))

        wrtr.writerow(['doctype', 'docid', 'result']
                      if options['autofix'] == True
                      else ['doctype', 'docid'])
        for matched_doc in docs:
            if options['autofix'] == True:
                sfm_doc = sfm.document(matched_doc.doc_type, matched_doc.doc_id)
                if sfm_doc[u'success'] == False:
                    fix_result = "No such document in SFM."
                elif sfm_doc[u'success'] == True:
                    if len(sfm_doc[u'text'].strip()) > 0:
                        matched_doc.text = sfm_doc[u'text']
                        matched_doc.save()
                        fix_result = "Added text of length {}".format(len(sfm_doc[u'text']))
                    else:
                        fix_result = "Document has no text in SFM."

                wrtr.writerow([matched_doc.doc_type, matched_doc.doc_id, fix_result])
            else:
                wrtr.writerow([matched_doc.doc_type, matched_doc.doc_id])



