from django.core.management.base import NoArgsCommand
from django.conf import settings
import superfastmatch

class Command(NoArgsCommand):
    help = 'Prints details about the superfastmatch servers specified in the configuration.'
    args = ''

    def handle(self, *args, **options):
        for (key, cfg) in settings.SUPERFASTMATCH.iteritems():
            print key
            print '  url: {0}'.format(cfg['url'])
            try:
                sfm = superfastmatch.DjangoClient(key, parse_response=True)
                documents = sfm.documents()
                if documents['success'] == True:
                    print '  documents: {0}'.format(documents['total'])
                else:
                    print '  Unable to query for documents.'
            except superfastmatch.SuperFastMatchError, e:
                print '  Unable to query for documents: {0}'.format(str(e))

            
