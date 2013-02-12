# -*- coding: utf-8 -*-

# Using the zipfile module from python 2.7 for backward compat with python 2.6
# See bug: http://bugs.python.org/issue7610
# Python 2.7.3 test_zipfile.py only fails two tests, both related to extracting
# directories, which we are not concerned with.
from zipfile27 import ZipFile
from contextlib import closing
try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Tells you how many documents are in a backup file.'
    args = '<file>'

    def handle(self, inpath, *args, **options):
        with closing(ZipFile(inpath, 'r')) as infile:
            with closing(infile.open('meta', 'r')) as metafile:
                metadata = pickle.load(metafile)
                print "Documents: {count}".format(**metadata)
                print "Doctypes: {doctypes}".format(**metadata)

