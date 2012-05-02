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
from django.core.management.base import BaseCommand

import progressbar
import progressbar.widgets

import superfastmatch


class UnpicklerIterator(object):
    def __init__(self, unpickler):
        self.unpickler = unpickler

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.unpickler.load()
        except EOFError:
            raise StopIteration


class Command(BaseCommand):
    help = 'Reads a backup file created by the livebackup command and POSTs the documents to the superfastmatch server.'
    args = '<file> <host> <port>'
    option_list = BaseCommand.option_list + (
        make_option('--doctypes',
                    action='store',
                    dest='doctypes',
                    default=None,
                    help='A mapping of doctypes to override the doctypes stored in the backup file. The pattern is from1:to1,from2:to2,...'),
        make_option('--dry-run',
                    action='store_true',
                    dest='dryrun',
                    default=False,
                    help='Read the backup file but don\'t actually post documents to the server.'),
    )

    def handle(self, inpath, host, port, *args, **options):
        try:
            port = int(port)
        except ValueError:
            print "The port must be numeric.".format(port)
            return

        if not (1 <= port <= 65535):
            print "The port must be between 1 and 65535."
            return

        if not os.path.exists(inpath):
            print "No such file: {0}".format(inpath)
            return

        doctype_mappings = {}
        doctypes_option = options.get('doctypes')
        if doctypes_option is not None:
            for mapping in doctypes_option.split(','):
                mapping = mapping.strip()
                (src, dst) = mapping.split(':')
                src = int(src)
                dst = int(dst)
                doctype_mappings[src] = dst

        if doctype_mappings:
            print >>sys.stderr, "Remapping doctypes:"
            for (src, dst) in doctype_mappings.iteritems():
                print >>sys.stderr, "    {0} => {1}".format(src, dst)

        url = 'http://{host}:{port}'.format(**locals())
        sfm = superfastmatch.Client(url)

        ignored_attributes = ['characters', 'id', 'defer']
        with closing(ZipFile(inpath, 'r')) as infile:
            with closing(infile.open('meta', 'r')) as metafile:
                metadata = pickle.load(metafile)
                progress = progressbar.ProgressBar(maxval=metadata['doc_count'],
                                                   widgets=[
                                                       progressbar.widgets.AnimatedMarker(),
                                                       '  ',
                                                       progressbar.widgets.Counter(),
                                                       '/{0}  '.format(metadata['doc_count']),
                                                       progressbar.widgets.Percentage(),
                                                       '  ',
                                                       progressbar.widgets.ETA(),

                                                   ])
                progress.start()
                doccounter = 0

                for file_number in range(0, metadata['file_count']):
                    docsfile_name = 'docs{num}'.format(num=file_number)
                    with closing(infile.open(docsfile_name, 'r')) as docsfile:

                        docloader = pickle.Unpickler(docsfile)
                        for doc in UnpicklerIterator(docloader):
                            if 'text' in doc and 'doctype' in doc and 'docid' in doc:
                                for attr in ignored_attributes:
                                    if doc.has_key(attr):
                                        del doc[attr]
                                new_doctype = doctype_mappings.get(doc['doctype'])
                                if new_doctype:
                                    doc['doctype'] = new_doctype
                                if options.get('dryrun') == False:
                                    add_result = sfm.add(defer=True, **doc)
                                    if add_result['success'] == False:
                                        print >>sys.stderr, "Failed to restore document ({doctype}, {docid})".format(**doc)
                            elif 'doctype' in doc and 'docid' in doc:
                                print >>sys.stderr, "Document ({doctype}, {docid}) cannot be restored because it is missing a text attribute.".format(**doc)

                            elif 'text' in doc:
                                print >>sys.stderr, "Document with text '{snippet}...' cannot be restored because it is missing a doctype and/or docid attribute.".format(snippet=doc['text'][:40])

                            else:
                                print >>sys.stderr, "Cannot restore empty document (missing all of text, doctype, and docid attributes)."

                            doccounter += 1
                            progress.update(doccounter)
                progress.finish()




