"""
This command is the complement of the restorebackup command. It 
iterates over documents on the server, pickles them, then dumps
them into a file and finally zips that file up with a small data
containing the number of documents, etc.
"""

import sys
import os
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
from contextlib import closing
try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.management.base import BaseCommand
import superfastmatch

class Command(BaseCommand):
    help = 'Dumps a set of documents from SuperFastMatch into a pickle file.'
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

            docs = superfastmatch.DocumentIterator(sfm, 
                                                   order_by='docid', 
                                                   doctype=doctype_rangestr,
                                                   chunksize=1000)

            metadata = {
                'count': 0,
                'doctypes': doctypes
            }
            ignored_attributes = ['characters', 'id']
           
            with NamedTemporaryFile(mode='wb') as metafile:
                with NamedTemporaryFile(mode='wb') as docsfile:
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
                            
                            pickle.dump(doc, docsfile, 1)
                            metadata['count'] += 1
                        else:
                            print >>sys.stderr, "Unable to fetch text for document ({doctype}, {docid})".format(**docmeta)

                    pickle.dump(metadata, metafile)
                    metafile.flush()
                    docsfile.flush()
                    with closing(ZipFile(outpath, 'w', ZIP_DEFLATED)) as outfile:
                        outfile.write(metafile.name, 'meta')
                        outfile.write(docsfile.name, 'docs')

            print "Dumped {count} documents spanning doctypes {doctypes}".format(**metadata)
