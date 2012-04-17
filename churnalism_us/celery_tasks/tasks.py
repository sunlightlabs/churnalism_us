from celery.task import task
from apiproxy.models import MatchedDocument
import superfastmatch

@task
def update_matches(results):
    
    sfm = superfastmatch.DjangoClient()
    
    for r in results:
        md = MatchedDocument.objects.get(doc_type=r['doctype'],
                                            doc_id=r['docid'])
        response = sfm.get(r['doctype'], r['docid'])
        print response 
        md.text = response['text']
        md.source_name = response['source']
        md.save()

