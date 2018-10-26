# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta

# use request var in templating language: http://stackoverflow.com/questions/
# 2882490/get-the-current-url-within-a-django-template
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
from django.utils.translation import ugettext_lazy

"""
Django settings for mysite project.
More info: https://docs.djangoproject.com/en/1.6/topics/settings/
Full list of settings: https://docs.djangoproject.com/en/1.6/ref/settings/
"""
import os
import sys


DEPLOYMENT = os.environ['DEPLOYMENT']
assert DEPLOYMENT in ['local', 'staging', 'live', 'maintenance', 'test', 'regtest'], DEPLOYMENT
if DEPLOYMENT == 'live':
    from web.settings_env.live import *
elif DEPLOYMENT == 'staging':
    from web.settings_env.staging import *
elif DEPLOYMENT == 'local':
    from web.settings_env.local import *
elif DEPLOYMENT == 'maintenance':
    from web.settings_env.maintenance import *
elif DEPLOYMENT == 'test':
    from web.settings_env.test import *
elif DEPLOYMENT == 'regtest':
    from web.settings_env.regtest import *

print "Using DEPLOYMENT level: " + DEPLOYMENT

# Be able to detect testing from inside django
TESTING = sys.argv[1:2] == ['test'] or 'py.test' in sys.argv[0]

#####################################################################
# General web settings
#####################################################################
ANONYMOUS_USER_ID = 1

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'test_without_migrations',
    'bootstrap3',
    'oauth2_provider',
    'corsheaders',
    'rest_framework',
    'django_extensions',
    'django_filters',
    'djcelery',
    'compressor',
    'rest_hooks',
    'acl',
    'applications',
    'bitcoin',
    'blobs',
    'coa',
    'emails',
    'encoder',
    'notifications',
    'note',
    'ownership',
    'piece',
    'prize',
    's3',
    'users',
    'util',
    'webhooks',
    'whitelabel',
    'whitelabel.cyland',
    'whitelabel.ikonotv',
    'whitelabel.market',
)

MIDDLEWARE_CLASSES = (
    'sslify.middleware.SSLifyMiddleware',  # should be 1st middleware class to ensure security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'subdomains.middleware.SubdomainURLRoutingMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

WSGI_APPLICATION = 'web.wsgi.application'

# URL for login
LOGIN_URL = '/art/home/'
ROOT_URLCONF = 'web.urls.ascribe'
SUBDOMAIN_URLCONFS = {
    None: 'web.urls.ascribe',
    'www': 'web.urls.ascribe',
    'api': 'web.urls.api',
    'api-staging': 'web.urls.api',
}
# SSL: Honor the 'X-Forwarded-Proto' header for request.is_secure(). Plays well with sslify.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # e.g. '/home/trentmc/code_ascribe/test_heroku/mysite'

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
# https://devcenter.heroku.com/articles/django-assets
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'compressor.finders.CompressorFinder',
)


# for files e.g. uploaded by user
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

APPEND_SLASH = True

# CORS
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'withcredentials',
    'cache-control',
    'cookie',
    'session-id'
)

# REST framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES':
        ('rest_framework.permissions.IsAuthenticated',
         'rest_framework.permissions.AllowAny',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour',
        'user': '10000/hour'},
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_METADATA_CLASS': 'web.apimetadata.SimpleMetadata',
}

if DEPLOYMENT in ['live']:
    REST_FRAMEWORK.update({'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',)})

FIXTURE_DIRS = (
    'web/api/v0_1/test/fixtures',
)

# OAUT Settings
OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
    },
    'CLIENT_ID_GENERATOR_CLASS': 'oauth2_provider.generators.ClientIdGenerator',
    'ACCESS_TOKEN_EXPIRE_SECONDS': 31536000  # 1 year
}

# Don't know why but withouth this you won't be able to run migrations
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

# https://github.com/evonove/django-oauth-toolkit/issues/204#issuecomment-77984967
MIGRATION_MODULES = {
    # key: app name, value: a fully qualified package name, not the usual `app_label.something_else`
    # lets store third app migrations in web/migrations
    'oauth2_provider': 'web.migrations.oauth2_provider',
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('fr', ugettext_lazy('French')),
    ('en', ugettext_lazy('English')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

#####################################################################
#  Bitcoin
#####################################################################

BTC_WALLET_BALANCE_THRESHOLD = 0.05  # if less than this number -> warning (accounts for dust unspents)
BTC_WALLET_NUM_UNSPENTS_THRESHOLD = 50  # if less than this number -> warning (about 50 transactions to go - if no dust)
# Editions.
# currently blockchain only allows about 3 'dust' outputs
MAX_NUM_EDITIONS = 100  # 1000 was suggested by Masha. This may be common for photography.

# Fees and token values in satoshi
BTC_FEE = 10000
BTC_TOKEN = 3000
BTC_CHUNK = 2160000


#####################################################################
#  Payment Processing
#####################################################################

# Payment processing: Stripe integration
STRIPE_AUTHORIZE_URL = 'https://connect.stripe.com/oauth/authorize'
STRIPE_ACCESS_TOKEN_URL = 'https://connect.stripe.com/oauth/token'
STRIPE_BASE_URL = 'https://api.stripe.com/'

# Payment processing: currencies. We further subset these based on where a user's stripe acct is.
CURRENCIES_ALLOWED = ['USD', 'EUR', 'GBP', 'CAD']

# Payment processing: fees
STRIPE_CHARGE_TRANSFER_AMOUNT_CENTS = 2500
STRIPE_CHARGE_TRANSFER_CURRENCY = 'EUR'

BASE_FEE_TO_STRIPE_CENTS = 30  # OBSOLETE
PERCENT_FEE_TO_STRIPE = 0.029
BASE_FEE_TO_ASCRIBE_CENTS = 20  # OBSOLETE
PERCENT_FEE_TO_ASCRIBE = 0.021  # OBSOLETE
PERCENT_EXCHANGE_FEE_TO_STRIPE = 0.02
MIN_PAYMENT_AMOUNT = 1.00  # This amt in USD, CAD, GPB, or EUR must be > stripe min of 0.50 USD

# Openexchangerates.org
# TODO do we need this?
OPEN_EXCHANGE_RATES_APP_ID = os.environ.get('OPEN_EXCHANGE_RATES_APP_ID', 'abc')

# TODO do we need this?
if STRIPE_LIVE_ENABLED:
    # Payment processing: Stripe integration
    ASCRIBE_STRIPE_CLIENT_ID = os.environ.get('STRIPE_CLIENT_LIVE_ID', 'abc')
    ASCRIBE_STRIPE_CLIENT_SECRET = os.environ.get('STRIPE_CLIENT_LIVE_SECRET', 'abc')
    ASCRIBE_STRIPE_CLIENT_PUBLIC = os.environ.get('STRIPE_CLIENT_LIVE_PUBLIC', 'abc')
else:
    # Payment processing: Stripe integration
    ASCRIBE_STRIPE_CLIENT_ID = os.environ.get('STRIPE_CLIENT_TEST_ID', 'abc')
    ASCRIBE_STRIPE_CLIENT_SECRET = os.environ.get('STRIPE_CLIENT_TEST_SECRET', 'abc')
    ASCRIBE_STRIPE_CLIENT_PUBLIC = os.environ.get('STRIPE_CLIENT_TEST_PUBLIC', 'abc')

#####################################################################
# Amazon AWS S3
#####################################################################

# Make caching expire 100 years in the future (ie always keep). Just in case files of the same
# name are uploaded in the future, model.py stores the files in unique subdirectories.
# http://streamhacker.com/2010/01/10/far-future-expires-header-wdjango-storages-s3/
# http://developer.yahoo.com/performance/rules.html#expires

many_years = date.today() + timedelta(days=365 * 100)
AWS_HEADERS = {
    'Expires': many_years.strftime('%a, %d %b %Y 20:00:00 GMT'),
}


# for amazon S3 storage
# http://stackoverflow.com/questions/10390244/how-to-set-up-a-django-project-with-django-storages-and-amazon-s3-but-with-diff
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = 'ascribe0'
AWS_PRESIGNED_URL_EXPIRY_TIME = 3600
AWS_S3_HOST = 's3-us-west-2.amazonaws.com'   # TODO put into env var

AWS_S3_SECURE_URLS = False  # use http instead of https
AWS_QUERYSTRING_AUTH = False  # don't add complex authentication-related query parameters for requests
AWS_MAX_SIZE = [50000000000, 500000, 5000000, 50000000]  # see fineuploader

AWS_BUCKET_DOMAIN = '{}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)
AWS_CLOUDFRONT_DOMAIN = 'd1qjsxua1o9x03.cloudfront.net'

# THUMBNAILS
THUMBNAIL_DEFAULT = 'media/thumbnails/ascribe_spiral.png'
THUMBNAIL_SIZES = {'100x100': (100, 100), '300x300': (300, 300), '600x600': (600, 600)}
THUMBNAIL_SIZE_DEFAULT = '300x300'

#####################################################################
#  Celery
#####################################################################

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
CELERY_RESULT_BACKEND_HOST = os.environ.get('CELERY_RESULT_BACKEND_HOST', 'localhost')
CELERY_RESULT_BACKEND_PORT = os.environ.get('CELERY_RESULT_BACKEND_PORT', 6379)
CELERY_RESULT_BACKEND_PASSWORD = os.environ.get('CELERY_RESULT_BACKEND_PASSWORD', '')
CELERY_RESULT_BACKEND_NAME = os.environ.get('CELERY_RESULT_BACKEND_NAME', '')
CELERY_RESULT_BACKEND = 'redis://{}:{}@{}:{}'.format(CELERY_RESULT_BACKEND_NAME,
                                                     CELERY_RESULT_BACKEND_PASSWORD,
                                                     CELERY_RESULT_BACKEND_HOST,
                                                     CELERY_RESULT_BACKEND_PORT)
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'Europe/Oslo'
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 3600
BROKER_POOL_LIMIT = 0

CELERY_ROUTES = ('util.routers.CeleryTaskRouter', )

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'


#####################################################################
#  Domain Constants
#####################################################################

# Jobs
JOB_BTC_TX, JOB_CONVERTVIDEO = "bitcoin tx", "convert video"

# Used for consign_status. http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way
NOT_CONSIGNED, PENDING_CONSIGN, CONSIGNED, PENDING_UNCONSIGN = 0, 1, 2, 3
CONSIGN_STATUS_CHOICES = ((NOT_CONSIGNED, '-'), (PENDING_CONSIGN, 'Pending consign'),
                          (CONSIGNED, 'Consigned'), (PENDING_UNCONSIGN, 'Pending unconsign'))


# Blocktrail
BLOCKTRAIL_API_KEY = os.environ['BLOCKTRAIL_API_KEY']
BLOCKTRAIL_API_SECRET = os.environ['BLOCKTRAIL_API_SECRET']


# Custom logging settings to show traceback in stdout

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'kpi_formatter': {
            'format': '%(name)s %(asctime)s %(message)s'
        },
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s'
                      ' (%(processName)s:%(process)d %(threadName)s:%(thread)d)'
                      ' %(name)s:%(lineno)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        },
        'console_simple': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'kpi_formatter',
        },
        'console_verbose': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'KPI': {
            'handlers': ['console_simple'],
            'level': 'INFO',
            'propagate': True,
        },
        'acl': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'bitcoin': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'blobs': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'coa': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'emails': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'encoder': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'notifications': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'ownership': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'piece': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'prize': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        's3': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'users': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'util': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'web': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'whitelabel': {
            'handlers': ['console_verbose'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

if DEPLOYMENT == 'local':
    LOGGING['handlers']['file'] = LOGGING_FILE_HANDLER
    for logger_attrs in LOGGING['loggers'].values():
        logger_attrs['handlers'].append('file')


HOOK_EVENTS = {
    # 'any.event.name': 'App.Model.Action' (created/updated/deleted)
    'share.webhook': 'ownership.Share.webhook',
    'consign.webhook': 'ownership.Consignment.webhook',
    'transfer.webhook': 'ownership.OwnershipTransfer.webhook',
    'loan.webhook': 'ownership.Loan.webhook'
}

HOOK_DELIVERER = 'webhooks.tasks.deliver_hook_wrapper'

PASSWORD_RESET_EXPIRATION_TIME = 1      # unit: hour
