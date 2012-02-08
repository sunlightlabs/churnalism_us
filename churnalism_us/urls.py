from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'churnalism_us.views.home', name='home'),
    # url(r'^churnalism_us/', include('churnalism_us.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^sidebyside/', include('sidebyside.urls')),
    url(r'^api/', include('apiproxy.urls')),
)

if settings.DEBUG:
    pattern = r'^{0}(?P<path>.*)$'.format(settings.STATIC_URL.lstrip('/'))
    urlpatterns += patterns('django.contrib.staticfiles.views',
                            url(pattern, 'serve'))
