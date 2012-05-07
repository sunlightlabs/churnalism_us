"""
This command is the complement of the restorebackup command. It 
iterates over documents on the server, pickles them, then dumps
them into a file and finally zips that file up with a small data
containing the number of documents, etc.
"""

import os
from django.core.management.base import BaseCommand, CommandError
from superfastmatch.util import parse_doctype_range
from superfastmatch.djangoclient import from_django_conf
from superfastmatch.tools.routines import backup


class Command(BaseCommand):
    help = 'Dumps a set of documents from SuperFastMatch into a pickle file.'
    args = '<server> <file> [doctypes]'

    def handle(self, server, outpath, doctype_rangestr=None, *args, **options):
        sfm = from_django_conf(server)
        
        if os.path.exists(outpath):
            raise CommandError("I have nothing against {0}, why would I overwrite it?".format(outpath))

        if doctype_rangestr is not None:
            parse_doctype_range(doctype_rangestr)
        backup(sfm, outpath, doctype_rangestr)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

