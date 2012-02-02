from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('apiproxy.views',
    url(r'^document/(\d+)/(\d+)/$', 'document'),
    url(r'^document/$', 'document_list'),
    url(r'^search/$', 'search'),
)


