import logging
from celery.task import task
from apiproxy.models import MatchedDocument
import superfastmatch

@task
def update_matched_document(doctype, docid):
    try:
        sfm = superfastmatch.DjangoClient()
        match_doc = MatchedDocument.objects.get(doc_type=doctype, doc_id=docid)
        sfm_doc = sfm.get(doctype, docid)
        match_doc.text = sfm_doc['text']
        match_doc.save()
    except superfastmatch.SuperFastMatchError, e:
        logging.warning('update_match({0!r}, {1!r}): {2!s}'.format(doctype, docid, e))
    except MatchedDocument.DoesNotExist:
        logging.warning('update_match({0!r}, {1!r}): No such MatchedDocument.'.format(doctype, docid))

