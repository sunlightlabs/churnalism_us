import os
from progressbar import ProgressBar, Percentage, Bar, ETA
from django.core.management.base import BaseCommand
from apiproxy.models import SearchDocument

class Command(BaseCommand):
    help = 'Iterate over all SearchDocument objects and write the text value to a file in a file named for the document UUID.'
    args = 'directory'

    def handle(self, directory, *args, **options):
        assert os.path.exists(directory)
        assert os.path.isdir(directory)

        progress = ProgressBar(maxval=SearchDocument.objects.count(),
                               widgets=[Percentage(), ' ', Bar(), ' ', ETA()]).start()

        for (idx, doc) in enumerate(SearchDocument.objects.all(), start=1):
            progress.update(idx)
            with file(os.path.join(directory, doc.uuid), 'w') as outf:
                outf.write(doc.text.encode('utf-8'))

        progress.finish()




