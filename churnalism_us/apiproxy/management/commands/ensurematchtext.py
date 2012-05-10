from django.core.management.base import NoArgsCommand
from django.db.models import Q
from apiproxy.models import MatchedDocument
from celery_tasks.tasks import update_matched_document

class Command(NoArgsCommand):
    help = 'Delete a SearchDocument instance by URL or UUID.'

    def handle(self, *args, **options):
        query = MatchedDocument.objects.filter(Q(text__isnull=True) | Q(text=''))

        cnt = query.count()
        print "{0} MatchedDocuments are missing text.".format(cnt)

        for match_doc in query:
                update_matched_document.delay(match_doc.doc_type, match_doc.doc_id)



