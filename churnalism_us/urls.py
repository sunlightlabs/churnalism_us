from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from churnalism_us.sitemap import GeneralSitemap
from sidebyside.sitemap import SidebysideSitemap

sitemaps = {
    'general': GeneralSitemap,
    'sidebyside': SidebysideSitemap
}

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'churnalism_us.views.home', name='home'),
    # url(r'^churnalism_us/', include('churnalism_us.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'sidebyside.views.search_page', name='index'),
    url(r'^about/$', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^404/$', direct_to_template, {'template': '404.html'}, name='404'),
    url(r'^contact/$', 'sidebyside.views.contact', name='contact'),
    url(r'^downloads/$', direct_to_template, {'template': 'downloads.html'}, name='downloads'),
    url(r'^beta/$', direct_to_template, {'template': 'beta.html'}, name='beta-instructions'),
    url(r'^sidebyside/', include('sidebyside.urls')),
    url(r'^api/', include('apiproxy.urls')),
    url(r'^cache/', include('django_memcached.urls')),
    url(r'^iframe/', direct_to_template, {'template': 'extension_iframe.html'}, name="iframe"),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)

