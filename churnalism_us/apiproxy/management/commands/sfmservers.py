import socket
from django.core.management.base import NoArgsCommand
from django.conf import settings
import superfastmatch
from superfastmatch.djangoclient import from_django_conf

class Command(NoArgsCommand):
    help = 'Prints details about the superfastmatch servers specified in the configuration.'
    args = ''

    def handle(self, *args, **options):
        for (key, cfg) in settings.SUPERFASTMATCH.iteritems():
            sfm = from_django_conf(key)
            try:
                if isinstance(sfm, superfastmatch.federated.FederatedClient):
                    print "{0} (federated)".format(key)
                    for (doctypes, client) in sfm.clients().iteritems():
                        print "  doctypes: {0}".format(doctypes.replace(':', ', '))
                        print "    url: {0}".format(client.url)
                        documents = client.documents(doctype=doctypes, order_by='docid', limit=1)
                        print "    documents: {0}".format(documents['total'])
                else:
                    print "{0}".format(key)
                    print '  url: {0}'.format(sfm.url)

                    documents = sfm.documents()
                    if documents['success'] == True:
                        print '  documents: {0}'.format(documents['total'])
                    else:
                        print '  Unable to query for documents.'
            except (superfastmatch.SuperFastMatchError, socket.error) as e:
                print '  Unable to query for documents: {0}'.format(str(e))

            
