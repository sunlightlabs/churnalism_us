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
    url(r'^(?P<uuid>[a-z0-9]{32})/textproblem/$', 'describe_text_problem', name='sidebyside-textproblem'),
    url(r'^search/$', 'search', name='sidebyside-search'),
    url(r'^shared/(?P<uuid>[a-z0-9]{32})/$', 'shared' , name='sidebyside-shared'),
    url(r'^confirmed/(?P<match_id>[0-9]+)/$', 'confirmed' , name='sidebyside-confirmed'),
    url(r'^firefox/parameters/$', 'ffext_parameters', name='sidebyside-ff-parameters'),
    url(r'^firefox/ribbon/$', 'ffext_ribbon', name='sidebyside-ff-ribbon'),
    url(r'^chrome/parameters/$', 'chromeext_parameters', name='sidebyside-chrome-parameters'),
    url(r'^chrome/ribbon/$', 'chromeext_ribbon', name='sidebyside-chrome-ribbon'),

    url(r'^ie9/ribbon/$', 'ie9ext_ribbon', name='sidebyside-ie9-ribbon'),
    url(r'^ie8/ribbon/$', 'ie8ext_ribbon', name='sidebyside-ie8-ribbon'),
    url(r'^loading/$', direct_to_template, {'template': 'sidebyside/loading.html'}, name='sidebyside-loading'),
    url(r'^ie_loading/$', direct_to_template, {'template': 'sidebyside/ie_loading.html'}, name='sidebyside-ie-loading'),
    url(r'^firefox/(?P<uuid>[a-z0-9]{32})/(?P<doctype>\d+)/(?P<docid>\d+)/$', 'ffext_recall', name='sidebyside-chrome-uuid-recall'),
    url(r'^chrome/(?P<uuid>[a-z0-9]{32})/(?P<doctype>\d+)/(?P<docid>\d+)/$', 'chromeext_recall', name='sidebyside-chrome-uuid-recall'),
    url(r'^generic/(?P<uuid>[a-z0-9]{32})/(?P<doctype>\d+)/(?P<docid>\d+)/$', 'generic_recall', name='sidebyside-generic')

)

