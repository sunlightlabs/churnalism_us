# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import superfastmatch
from apiproxy.views import execute_search, record_matches
from apiproxy.models import SearchDocument

def prune_old_matches(search_doc, search_results):
    rows = search_results['documents']['rows']
    docpairs = [(row['doctype'], row['docid'])
                for row in rows]

    matches = search_doc.match_set.all()
    for match in matches:
        md = match.matched_document
        if (md.doc_type, md.doc_id) not in docpairs:
            print u"Deleting match: {0} => {1}".format(search_doc, md)
            match.delete()

class Command(BaseCommand):
    help = 'Update database objects to reflect updated coverage calcualtions.'
    args = ''

    def handle(self, *args, **options):
        self.sfm = superfastmatch.DjangoClient()

        for search_doc in SearchDocument.objects.all():
            print u"Updating {0}: {1}".format(search_doc.uuid, search_doc.title or "(untitled)")
            response = execute_search(search_doc)
            record_matches(search_doc, response, update_matches=True)
            prune_old_matches(search_doc, response)

