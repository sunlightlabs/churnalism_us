# -*- coding: utf-8 -*-

import sys
import os
from time import sleep
from optparse import make_option
# Using the zipfile module from python 2.7 for backward compat with python 2.6
# See bug: http://bugs.python.org/issue7610
# Python 2.7.3 test_zipfile.py only fails two tests, both related to extracting
# directories, which we are not concerned with.
from zipfile27 import ZipFile
from contextlib import closing
from pprint import pprint
try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.management.base import BaseCommand, CommandError

import progressbar
import progressbar.widgets

from superfastmatch.djangoclient import from_django_conf
from superfastmatch.tools.routines import restore


class Command(BaseCommand):
    help = 'Reads a backup file created by the livebackup command and POSTs the documents to the superfastmatch server.'
    args = '<server> <file>'
    option_list = BaseCommand.option_list + (
        make_option('--doctypes',
                    action='store',
                    dest='doctypes',
                    default=None,
                    help='A mapping of doctypes to override the doctypes stored in the backup file. The pattern is from1:to1,from2:to2,...'),
        make_option('--dryrun',
                    action='store_true',
                    dest='dryrun',
                    default=False,
                    help='Read the backup file but don\'t actually post documents to the server.'),
    )

    def handle(self, server, inpath, *args, **options):
        if not os.path.exists(inpath):
            raise CommandError("No such file: {0}".format(inpath))

        sfm = from_django_conf(server)
        restore(sfm, inpath, doctype_mappingstr=options.get('doctypes'), dryrun=options.get('dryrun'))


