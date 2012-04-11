import sys
import os
from pprint import pprint
try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.management.base import BaseCommand
import superfastmatch

class Command(BaseCommand):
    help = 'Dumps a set of documents from SuperFastMatch into a JSON file, similar to a Django fixture.'
    args = '<file> <host> <port>'

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

        url = 'http://{host}:{port}'.format(**locals())
        sfm = superfastmatch.Client(url)

        ignored_attributes = ['characters', 'id', 'defer']
        with file(inpath, 'rb') as infile:
            docloader = pickle.Unpickler(infile)
            try:
                while True:
                    doc = docloader.load()
                    if 'text' in doc and 'doctype' in doc and 'docid' in doc:
                        for attr in ignored_attributes:
                            if doc.has_key(attr):
                                del doc[attr]
                        add_result = sfm.add(defer=True, **doc)
                        if add_result['success'] == False:
                            print >>sys.stderr, "Failed to restore document ({doctype}, {docid})".format(**doc)
                    elif 'doctype' in doc and 'docid' in doc:
                        print >>sys.stderr, "Document ({doctype}, {docid}) cannot be restored because it is missing a text attribute.".format(**doc)

                    elif 'text' in doc:
                        print >>sys.stderr, "Document with text '{snippet}...' cannot be restored because it is missing a doctype and/or docid attribute.".format(snippet=doc['text'][:40])

                    else:
                        print >>sys.stderr, "Cannot restore empty document (missing all of text, doctype, and docid attributes)."

            except EOFError:
                pass



