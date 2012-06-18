from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'churnalism_us.views.home', name='home'),
    # url(r'^churnalism_us/', include('churnalism_us.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'sidebyside.views.search_page', name='index'),
    url(r'^about/$', direct_to_template, {'template': 'about.html', 'extra_context': {'ABSOLUTE_STATIC_URL': settings.DOMAIN + settings.STATIC_URL}}, name='about'),
    url(r'^contact/$', direct_to_template, {'template': 'contact.html', 'extra_context':{ 'ABSOLUTE_STATIC_URL': settings.DOMAIN + settings.STATIC_URL}}, name='contact'),
    url(r'^downloads/$', direct_to_template, {'template': 'downloads.html', 'extra_context':{ 'ABSOLUTE_STATIC_URL': settings.DOMAIN + settings.STATIC_URL}}, name='downloads'),
    url(r'^sidebyside/', include('sidebyside.urls')),
    url(r'^api/', include('apiproxy.urls')),
    url(r'^submitcontact/', 'sidebyside.views.contact_submission', name='contact-submission'),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

