"""
The apiproxy app mimics the read-only portions of the Superfastmatch API.
"""

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'apiproxy.views',

    url(r'^document/(\d+)/(\d+)/$', 'document'),
    url(r'^document/(\d+)/$', 'document_list'),
    url(r'^document/$', 'document_list'),
    url(r'^association/$', 'association'),
    url(r'^search/$', 'search'),
    url(r'^search/(?P<doctype>[\d:]+)/$', 'search'),

    url(r'^mimicry/document/(\d+)/(\d+)/$', 'mimicked_document'),
    url(r'^mimicry/document/(\d+)/$', 'mimicked_document_list'),
    url(r'^mimicry/document/$', 'mimicked_document_list'),
    url(r'^mimicry/search/$', 'mimicked_search'),


    # TODO: The Superfastmatch API does not provide a JSON 
    #       representation for these yet so there isn't much
    #       to gain by exposing them.
    # url(r'^index/$', 'index'),
    # url(r'^status/$', 'status'),
    # url(r'^queue/(\d+)/$', 'queue'),
    # url(r'^queue/$', 'queue'),
)


