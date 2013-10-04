# -*- coding: utf-8 -*-

from __future__ import division, print_function

import time
import os
import logging

from optparse import make_option

from django.core.management.base import CommandError

import unicodecsv
import superfastmatch
from apiproxy.models import Match
from utils.mgmt import LoggableMgmtCommand

def document_exists(sfm, doctype, docid):
    doc = sfm.document(doctype, docid)
    return u'success' in doc and doc[u'success'] == True

def delete_matches_for_document(doctype, docid):
    matches = (Match.objects
                    .select_related('search_document', 'matched_document')
                    .filter(matched_document__doc_type=doctype,
                            matched_document__doc_id=docid))
    for m in matches:
        logging.warn(u"Deleting match between {uuid} and ({doctype},{docid})".format(doctype=doctype, docid=docid, uuid=m.search_document.uuid))
        m.matched_document.delete()
        m.delete()

class Command(LoggableMgmtCommand):
    help = """Iterates over a delete schedule (created by export_delete_schedule) and safely deletes documents from superfastmatch along with the corresponding database artifacts."""
    args = 'path'
    option_list = LoggableMgmtCommand.option_list + (
        make_option('--dryrun',
                    action='store_true',
                    dest='dryrun',
                    default=False,
                    help='Don\'t actually delete anything, just report what would be deleted.'),
    )

    def handle(self, inpath=None, *args, **options):
        super(Command, self).handle(*args, **options)

        if inpath is None:
            raise CommandError(u"You must specify an input file.")

        if not os.path.exists(inpath):
            raise CommandError(u"File does not exist: {}".format(inpath))

        sfm = superfastmatch.from_django_conf()

        prev_docpair = None
        with open(inpath, 'rb') as outfile:
            rdr = unicodecsv.DictReader(outfile)

            for (idx, docrow) in enumerate(rdr):
                docpair = (int(docrow['doctype']), int(docrow['docid']))
                logging.warn(u"Deleting superfastmatch document {}".format(docpair))
                if options['dryrun'] == False:
                    sfm.delete(*docpair)

                # Poll on and delete the previous document
                if idx > 0:
                    logging.warn(u"Deleting matches for {}".format(prev_docpair))
                    if options['dryrun'] == False:
                        while document_exists(sfm, *prev_docpair) == True:
                            logging.info(u"Polling on document {}".format(prev_docpair))
                            time.sleep(1)
                        delete_matches_for_document(*prev_docpair)

                prev_docpair = docpair

