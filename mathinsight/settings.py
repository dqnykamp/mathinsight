# Django settings for mathinsight project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ADMINS = (
    ('Duane Nykamp', 'nykamp@umn.edu'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mathinsight',
        'USER': 'mathinsight_web',
        'PASSWORD': '!web@access#ornery$',
    }
}
MEDIA_ROOT = '/home/nykamp/web/html/media/'
MEDIA_URL = '/site_media/'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': '/home/nykamp/web/mathinsight/mathinsightdatabase.sql'
#     }
# }
# MEDIA_ROOT = '/home/nykamp/web/mathinsight/fakemedia/'
# MEDIA_URL = '/site_fakemedia/'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


#STATIC_ROOT = '/home/nykamp/web/mathinsight/static/'
STATIC_ROOT = '/home/nykamp/web/mathinsight_static2/'

STATIC_URL = '/static/'

#BASE_URL = 'http://mathinsight.org'
BASE_URL = 'http://localhost'

# subdirectory in which to upload images.  Use a trailing slash
IMAGE_UPLOAD_TO = "image/"

# subdirectory in which to upload applet.  Use a trailing slash
APPLET_UPLOAD_TO = "applet/"

# subdirectory in which to upload video.  Use a trailing slash
VIDEO_UPLOAD_TO = "video/"

# subdirectory in which to upload auxiliary files.  Use a trailing slash
AUXILIARY_UPLOAD_TO = "auxiliary/"

LOGIN_REDIRECT_URL = '/course/'
LOGIN_URL = '/accounts/login'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 's!oowznnliax$5v$negxd6c)ah#qei)qkt6s$hx%t4mj800*(*'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages'
)

MIDDLEWARE_CLASSES = (
    #'djangovalidation.middleware.HTMLValidationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    )

ROOT_URLCONF = 'mathinsight.urls'

WSGI_APPLICATION = 'mathinsight.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'dajaxice.finders.DajaxiceFinder',
)

SITE_ID = 2

SESSION_COOKIE_AGE = 31536000

EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_USER='snykamp@gmail.com'
EMAIL_HOST_PASSWORD='dq&slfe'
EMAIL_PORT=587
EMAIL_USE_TLS=True
SERVER_EMAIL='webserver@mathinsight.org'
DEFAULT_FROM_EMAIL='webserver@mathinsight.org'
#SEND_BROKEN_LINK_EMAILS=True

HTML_VALIDATION_URL_IGNORE=['^/admin/','^/search/']

import os
HAYSTACK_DEFAULT_OPERATOR = 'OR'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}



HITCOUNT_KEEP_HIT_ACTIVE = { 'days': 0 }
HITCOUNT_HITS_PER_IP_LIMIT = 0
#HITCOUNT_EXCLUDE_USER_GROUP = ( 'Editor', )


COMMENTS_APP = 'micomments'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.redirects',
    'dajaxice',
    'dajax',
    'micomments',
    'micourses',
    'midocs',
    'mitesting',
    'mithreads',
    'haystack',
    'hitcount',
    'reversion',
#    'umnmimic',
    'south',
)
