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
    args = '<file> [doctypes]'

    def handle(self, outpath, doctype_rangestr, *args, **options):
        sfm = superfastmatch.DjangoClient()
        
        if not doctype_rangestr:
            print "It's usually not a good idea to dump all documents."
        else:
            if os.path.exists(outpath):
                print "I have nothing against {0}, why would I overwrite it?".format(outpath)
                return

            doctypes = superfastmatch.parse_doctype_range(doctype_rangestr)

            print 'doctype_rangestr = ' + doctype_rangestr

            docs = superfastmatch.DocumentIterator(sfm, 
                                                   order_by='docid', 
                                                   doctype=doctype_rangestr,
                                                   chunksize=1000)

            metadata = {
                'count': 0,
                'doctypes': doctypes
            }
            ignored_attributes = ['characters', 'id']
            with file(outpath, 'wb') as outfile:
                for docmeta in docs:
                    if not docmeta:
                        print >>sys.stderr, "Dropped empty document."
                        continue

                    docresult = sfm.document(docmeta['doctype'], docmeta['docid'])
                    if docresult['success'] == True:
                        doc = {}
                        doc.update(docmeta)
                        for attr in ignored_attributes:
                            if attr in doc:
                                del doc[attr]
                        doc['text'] = docresult['text']
                        
                        pickle.dump(doc, outfile)
                        metadata['count'] += 1
                    else:
                        print >>sys.stderr, "Unable to fetch text for document ({doctype}, {docid})".format(**docmeta)

            print repr(metadata)

