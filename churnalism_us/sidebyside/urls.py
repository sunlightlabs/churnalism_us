from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('sidebyside.views',
    # Examples:
    # url(r'^$', 'sfm_us_site.views.home', name='home'),
    # url(r'^sfm_us_site/', include('sfm_us_site.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'search_page', name='sidebyside-search-page'),
    url(r'^(?P<uuid>[a-z0-9]{32})/$', 'search', name='sidebyside-uuid-search'),
    url(r'^(?P<uuid>[a-z0-9]{32})/(?P<doctype>\d+)/(?P<docid>\d+)/$', 'permalink', name='sidebyside-permalink'),
    url(r'^search/$', 'search', name='sidebyside-search'),
    url(r'^shared/(?P<uuid>[a-z0-9]{32})/$', 'shared' , name='sidebyside-shared'),
    url(r'^confirmed/(?P<match_id>[0-9]+)/$', 'confirmed' , name='sidebyside-confirmed'),
    url(r'^chrome/(?P<uuid>[a-z0-9]{32})/$', 'chromeext_recall', name='sidebyside-chrome-uuid-recall'),
    url(r'^generic/(?P<match_doc_type>\d+)/(?P<match_doc_id>\d+)/(?P<search_uuid>[a-z0-9]{32})/$', 'sidebyside_generic', name='sidebyside-generic')

)

