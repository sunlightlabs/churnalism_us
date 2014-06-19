# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import logging
import datetime

from optparse import make_option

from django.core.management.base import CommandError
from django.db.models import Count, Q

import dateutil.parser

from apiproxy.models import Match, SearchDocument
from utils.mgmt import LoggableMgmtCommand

from django.conf import settings

class Command(LoggableMgmtCommand):
    help = 'Exports a CSV of documents that can be deleted from superfastmatch because they do not sufficiently match any searches (use delete_documents command to actually delete them).'
    args = 'doctype output_file.csv'
    option_list = LoggableMgmtCommand.option_list + (
        make_option('--report-date',
                    action='store',
                    dest='report_date',
                    help='Last date to be included in the report.'),
    )

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        if options.get('report_date') is not None:
            report_date = dateutil.parser.parse(options['report_date']).date()
            if report_date >= datetime.date.today():
                print(u"It's generally a bad idea to try to report metrics for days that have not yet passed since they could change.")
        else:
            report_date = datetime.date.today() - datetime.timedelta(days=1)
        report_date = report_date.isoformat()

        print(u"Generating report for", report_date)
        print(u"This will take a few minutes.")

        minimum_pct = settings.SIDEBYSIDE['minimum_coverage_pct']
        minimum_chars = settings.SIDEBYSIDE['minimum_coverage_chars']
        sites = len(Match.objects.filter(~Q(search_document__url=''),
                                         created__lte=report_date,
                                         search_document__domain__isnull=False,
                                         search_document__url__isnull=False,
                                         search_document__title__isnull=False,
                                         overlapping_characters__gte=minimum_chars,
                                         percent_churned__gte=minimum_pct)
                    .values('search_document__domain')
                    .annotate(cnt=Count('pk'))
                    .order_by('-cnt')
                    .filter(cnt__gt=1))


        documents = (SearchDocument.objects.filter(~Q(url=''),
                                                   url__isnull=False,
                                                   created__lte=report_date).count())

        print(u"Number of sites with matches:", sites)
        print(u"Number of documents searched:", documents)



