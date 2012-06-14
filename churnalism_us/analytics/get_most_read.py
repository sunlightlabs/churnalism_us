
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
from analytics import sample_utils
from datetime import datetime, timedelta
from apiclient.errors import HttpError
from oauth2client.client import AccessTokenRefreshError


# The table ID is used to identify from which Google Anlaytics profile
# to retrieve data. This ID is in the format ga:xxxx where xxxx is the
# profile ID.
TABLE_ID = 'ga:60763489'


def get_most_viewed():
    #sample_utils.process_flags()

    # Authenticate and construct service.
    service = sample_utils.initialize_service()

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



