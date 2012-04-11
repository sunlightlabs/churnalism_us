import sys
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.management.base import BaseCommand
import superfastmatch

class Command(BaseCommand):
    help = 'Dumps a set of documents from SuperFastMatch into a JSON file, similar to a Django fixture.'
    args = '<file> [doctype1 [doctype2 [...]]]'

    def handle(self, outpath, *args, **options):
        sfm = superfastmatch.DjangoClient()
        
        if len(args) == 0:
            print "It's usually not a good idea to dump all documents."
        else:
            if os.path.exists(outpath):
                print "I have nothing against {0}, why would I overwrite it?".format(outpath)
                return

            doctype_rngstr = args[0]

            docs = superfastmatch.DocumentIterator(sfm, 
                                                   order_by='docid', 
                                                   doctype=doctype_rngstr, 
                                                   chunksize=1000)

            ignored_attributes = ['characters', 'id']
            with file(outpath, 'wb') as outfile:
                for docmeta in docs:
                    docresult = sfm.document(docmeta['doctype'], docmeta['docid'])
                    if docresult['success'] == True:
                        doc = {}
                        doc.update(docmeta)
                        for attr in ignored_attributes:
                            del doc[attr]
                        doc['text'] = docresult['text']
                        
                        pickle.dump(doc, outfile)
                    else:
                        print >>sys.stderr, "Unable to fetch text for document ({doctype}, {docid})".format(**docmeta)

