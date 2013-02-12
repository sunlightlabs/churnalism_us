from django.core.management.base import NoArgsCommand
import superfastmatch


def freq(it):
    counts = {}
    for x in it:
        cnt = counts.get(x, 0)
        counts[x] = cnt + 1
    return counts


class Command(NoArgsCommand):
    help = 'Prints a pretty version of the underlying /queue/ results.'
    args = ''

    def handle(self, *args, **options):
        sfm = superfastmatch.DjangoClient('default', parse_response=True)
        response = sfm.queue()

        if response['success'] == True:
            queued = [r for r in response['rows'] if r['status'] == 'Queued']
            active = [r for r in response['rows'] if r['status'] == 'Active']

            print 'Length: {0}{1}'.format(len(queued) + len(active),
                                          '' if response.get('cursors', {}).get('next') == '' else '+')
            for (action, cnt) in freq([r['action'] for r in queued]).iteritems():
                print '  {action!s:<20}  {cnt!s:>10}'.format(action=action, cnt=cnt)

            if len(active) == 0:
                print 'No active tasks'
            else:
                print 'Active task(s):'
                for r in active:
                    fmtstr = '  Task #{id}: {action} (priority {priority})'
                    if r['action'] == 'Add Association':
                        fmtstr += ' for document ({doctype}, {docid})'
                    elif r['action'] == 'Add Associations':
                        fmtstr += ' from {source} => {target}'
                    
                    print fmtstr.format(**r)
            

