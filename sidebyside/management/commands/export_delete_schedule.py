# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import logging

from optparse import make_option

from django.core.management.base import CommandError

import unicodecsv
import superfastmatch

from apiproxy.models import Match
from utils.mgmt import LoggableMgmtCommand

from django.conf import settings

class Command(LoggableMgmtCommand):
    help = 'Exports a CSV of documents that can be deleted from superfastmatch because they do not sufficiently match any searches (use delete_documents command to actually delete them).'
    args = 'doctype output_file.csv'
    option_list = LoggableMgmtCommand.option_list + (
        make_option('--apply-sidebyside-thresholds',
                    action='store_true',
                    dest='apply_sidebyside_thresholds',
                    default=False,
                    help='Delete documents matched by apiproxy but filtered out of user-facing results by the sidebyside app.'),
    )

    def handle(self, doctype, outpath=None, *args, **options):
        super(Command, self).handle(*args, **options)

        if doctype is None:
            raise CommandError(u"You must specify a doctype to prune.")
        try:
            doctype = int(doctype)
        except ValueError:
            raise CommandError(u"The doctype must be an integer.")

        if outpath is None:
            raise CommandError(u"You must specify an output file.")

        if os.path.exists(outpath):
            raise CommandError(u"File already exists: {}".format(outpath))

        if options['apply_sidebyside_thresholds'] == True:
            minimum_pct = settings.SIDEBYSIDE['minimum_coverage_pct']
            minimum_chars = settings.SIDEBYSIDE['minimum_coverage_chars']

        sfm = superfastmatch.from_django_conf()

        docs = superfastmatch.DocumentIterator(sfm, 'docid',
                                               doctype=doctype,
                                               fetch_text=False)

        with open(outpath, 'wb') as outfile:
            wrtr = unicodecsv.DictWriter(outfile, ['doctype',
                                                   'docid'])
            wrtr.writeheader()

            for doc in docs:
                apiproxy_matches = list(Match.objects.filter(matched_document__doc_type=doctype,
                                                             matched_document__doc_id=doc['docid']))
                sidebyside_matches = []
                if options['apply_sidebyside_thresholds'] == True:
                    sidebyside_matches = [m
                                          for m in apiproxy_matches
                                          if m.overlapping_characters >= minimum_chars
                                          and m.percent_churned >= minimum_pct]

                if (len(apiproxy_matches) == 0) or (options['apply_sidebyside_thresholds'] == True and len(sidebyside_matches) == 0):
                    if options['apply_sidebyside_thresholds'] == True:
                        for m in apiproxy_matches:
                            logging.info(u"Scheduling deletion for match between {uuid} and ({doctype},{docid}) because it matches {uuid} with [{chars},{pct}%]".format(uuid=m.search_document.uuid, doctype=m.matched_document.doc_type, docid=m.matched_document.doc_id, chars=m.overlapping_characters, pct=m.percent_churned))
                    logging.info(u"Scheduling deletion for document ({doctype},{docid})".format(**doc))
                    wrtr.writerow({'doctype': doc['doctype'], 'docid': doc['docid']})

                else:
                    for m in sidebyside_matches or apiproxy_matches:
                        logging.info(u"Skipping deletion of document ({doctype},{docid}) because it matches {uuid} with [{chars},{pct}%]".format(doctype=doc['doctype'], docid=doc['docid'], uuid=m.search_document.uuid, chars=m.overlapping_characters, pct=m.percent_churned))

        file_status = os.stat(outpath)
        print(u"{sz!s: >12} {path}".format(sz=file_status.st_size, path=outpath))
