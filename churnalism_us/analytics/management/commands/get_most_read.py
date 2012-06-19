
# Adapted from core_reporting_v3_referency.py in the google api python client, 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import analytics_utils
from datetime import datetime, timedelta
from apiclient.errors import HttpError
from oauth2client.client import AccessTokenRefreshError
from django.core.management.base import BaseCommand
from apiproxy.models import SearchDocument, MatchedDocument, Match
import pickle
import settings

# The table ID is used to identify from which Google Anlaytics profile
# to retrieve data. This ID is in the format ga:xxxx where xxxx is the
# profile ID.
TABLE_ID = 'ga:60763489'

def get_most_viewed():
    #sample_utils.process_flags()

    # Authenticate and construct service.
    service = analytics_utils.initialize_service()

    # Try to make a request to the API. Print the results or handle errors.
    results = get_api_query(service).execute()
    return get_rows(results)

def get_api_query(service):
    """Gets top numbers of unique events for 
        each document_uuid for the past month.
        used to populate most read/viewed.
    """
    today = datetime.now()
    month_ago = today - timedelta(30)

    today_fmt = today.strftime("%Y-%m-%d")
    month_ago_fmt = month_ago.strftime("%Y-%m-%d")

    return service.data().ga().get(
        ids=TABLE_ID,
        start_date=month_ago_fmt,
        end_date=today_fmt,
        metrics='ga:uniqueEvents',
        dimensions='ga:customVarValue1',
        sort='-ga:uniqueEvents',
        start_index='1',
        max_results='10')

def get_rows(results):
    ids = []
    if results.get('rows', []):
        for row in results.get('rows'):
            ids.append(row[0])
    return ids

def most_read(number_viewed):
    churns = []
    data = get_most_viewed()
    for d in data:
        params = d.split('_')
        if len(params) > 2: #should have a uuid, doctype and doc id
            uuid = params[0]
            doctype = params[1]
            docid = params[2]
            
            try:
                searchdoc = SearchDocument.objects.get(uuid=uuid)
                matchdoc = MatchedDocument.objects.get(doc_id=docid, doc_type=doctype)
                match = Match.objects.filter(search_document=searchdoc, matched_document=matchdoc, percent_churned__gte=settings.SIDEBYSIDE.get('minimum_coverage_pct', 0), overlapping_characters__gte=settings.SIDEBYSIDE.get('minimum_coverage_chars', 0)).order_by('-percent_churned')[:20]
                if len(match) > 0:
                    match = match[0]

                    churns.append({'percent': match.percent_churned, 
                                'title':searchdoc.title, 
                                'text': searchdoc.text, 
                                'uuid': searchdoc.uuid,
                                'doctype': matchdoc.doc_type,
                                'docid': matchdoc.doc_id})
            except MatchedDocument.DoesNotExist:
                continue
            except SearchDocument.DoesNotExist:
                continue
    
    #serialize this data
    pickle.dump(churns, open(settings.PROJECT_ROOT + '/analytics/management/commands/most_read.dat', 'w'))
     
class Command(BaseCommand):
    help = 'Get the analytics stats'
    args = ''

    def handle(self, *args, **options):

        most_read(4)
