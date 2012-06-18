# Django settings for churnalism_us project.

import os
import djcelery
from datetime import timedelta

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DOMAIN = 'http://us.churnalism.com'
DEBUG = True

djcelery.setup_loader()

BROKER_URL = "amqp://guest:guest@localhost:5672/"

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kaitlin Lee','klee@sunlightfoundation.com'),
    ('timball', 'tball@sunlightfoundation.com'),
    ('Drew Vogel', 'dvogel@sunlightfoundation.com'),
)

ADMIN_EMAILS = ('klee@sunlightfoundation.com', 'dvogel@sunlightfoundation.com')
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, '..', '.static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'static'),
    os.path.join(PROJECT_ROOT, 'sidebyside', 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'l2zid4jkk1bkmd@me+)w5qcux0fjto2n8xxcu=#_*s9cgl#m-#'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'generictags.absolutestaticurl.absolutestaticurl',
    'generictags.baseurl.baseurl',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INTERNAL_IPS = ('127.0.0.1', )

ROOT_URLCONF = 'churnalism_us.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates')
)

DEVSERVER_DEFAULT_PORT = '7000'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'debug_toolbar',

    # devserver provides a threaded/forked replacement for runserver
    # This enables the server to handle simultaneous requests, which is
    # required by the sidebyside app, since it dogfoods the apiproxy app.
    'devserver',

    'gunicorn',
    'generictags',
    'sidebyside',
    'apiproxy',
    'djcelery',
    'kombu.transport.django',
    'celery_tasks',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


#EMAIL_HOST = 'smtp.postmarkapp.com'
#EMAIL_HOST_USER = '8775185c-f59c-4a2e-8ae3-4950f6cd66eb'
#EMAIL_HOST_PASSWORD = '8775185c-f59c-4a2e-8ae3-4950f6cd66eb'
EMAIL_BACKEND = 'postmark.backends.PostmarkBackend'
POSTMARK_API_KEY = '8775185c-f59c-4a2e-8ae3-4950f6cd66eb'


SIDEBYSIDE = {
    'max_doc_prefetch': 0,
    'minimum_coverage_pct': 0,  # Plain-english percentages, e.g. 3 = 3%
    'minimum_coverage_chars': 0
}

APIPROXY = {
    'document_timeout': timedelta(hours=4),
    'proper_noun_threshold': 0.8,
    'commonality_threshold': 0.3,
    'embellishments': {
        'reduce_frags': False,
        'add_coverage': True,
        'add_density': True,
        'add_snippets': True,
        'prefetch_documents': False
    }
}

SUPERFASTMATCH = {
    'default': {
        # This should point at a Superfastmatch server
        'url': 'http://127.0.0.1:8080',
        'parse_response': True
    },
    'sidebyside': {
        # This should point at a running instance of apiproxy app
        'url': 'http://127.0.0.1:7000/api',
        'parse_response': True
    }
}

try:
    from local_settings import *
except ImportError, exp:    
    pass


