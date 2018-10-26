# -*- coding: utf-8 -*-
"""
Local settings
"""

from __future__ import absolute_import

import os

from .bitcoin_settings import *     # noqa
from .common import *   # noqa


# governs main settings. Local & staging are for devel. Staging & live are online. Live=production.
DEBUG = True
TEMPLATE_DEBUG = True

# Services
BTC_ENABLED = False
BTC_SERVICE = 'daemon'

# SSL: sslify
SSLIFY_ENABLE = False
SSLIFY_DISABLE = not SSLIFY_ENABLE

STRIPE_LIVE_ENABLED = False
if STRIPE_LIVE_ENABLED:
    assert SSLIFY_ENABLE == STRIPE_LIVE_ENABLED

# Host and Django settings
ASCRIBE_SCHEME = os.environ.get('ASCRIBE_SCHEME', 'http')
ASCRIBE_HOST = os.environ.get('ASCRIBE_HOST', 'localhost.com')
ASCRIBE_PORT = os.environ.get('PORT', '8000')
ASCRIBE_URL = '{}://{}:{}/'.format(ASCRIBE_SCHEME, ASCRIBE_HOST, ASCRIBE_PORT)
ASCRIBE_URL_NO_APP = ASCRIBE_URL
ASCRIBE_URL_FRONTEND = os.environ.get('ASCRIBE_URL_FRONTEND',
                                      'http://{}:3000/'.format(ASCRIBE_HOST))
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

SITE_ID = 2
###################
#  Services
###################
ZENCODER_API_KEY = os.environ['ZENCODER_API_KEY_TEST']
# PDF
ASCRIBE_PDF_URL = 'https://ascribepdf-staging.herokuapp.com'
# ASCRIBE_PDF_URL = 'http://localhost:9000'


# Bitcoin
# BTC_MAIN_WALLET = '12udvE3zmbQLhtSGZUqqAvGWSKDUCpbgoq'
# DJANGO_PYCOIN_ADMIN_PASS = 'REDACTED'

BTC_MAIN_WALLET = TESTNET_FEDERATION_ADDRESS
DJANGO_PYCOIN_ADMIN_PASS = TESTNET_FEDERATION_PASSWORD
BTC_REFILL_ADDRESS = TESTNET_REFILL_ADDRESS
BTC_REFILL_PASSWORD = TESTNET_REFILL_PASSWORD

BTC_USERNAME = TESTNET_USERNAME
BTC_PASSWORD = TESTNET_PASSWORD
BTC_HOST = TESTNET_HOST
BTC_PORT = TESTNET_PORT
BTC_TESTNET = True
# DJANGO_PYCOIN_ADMIN_PASS = os.environ['DJANGO_PYCOIN_ADMIN_PASS']

# TODO move this to a test settings to differentiate between test & dev (local)
CELERY_ALWAYS_EAGER = True

# for amazon S3 storage
# http://stackoverflow.com/questions/10390244/how-to-set-up-a-django-project-with-django-storages-and-amazon-s3-but-with-diff
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = 'ascribe0'

CSRF_COOKIE_NAME = 'csrftoken2'
CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.localhost.com')
SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', '.localhost.com')

CORS_ORIGIN_WHITELIST = (
    'ascribe-jsapp.herokuapp.com',
    'giano-staging.herokuapp.com',
    'localhost:3000',
    'localhost:9000',
    ASCRIBE_HOST + ':3000',
)

CORS_ORIGIN_REGEX_WHITELIST = (
    '^(https?://)?(\w+\.)?localhost\.com:3000$',
    '^(https?://)?(\w+\.)?spool\.ascribe:3000$',
)

###################
#  Database
###################
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
# https://devcenter.heroku.com/articles/heroku-postgresql
DATABASES = {
    # Use my local installation of postgresql. Works on both svn and git-heroku codebases.
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mysite_db',
        'USER': 'mysite_user',
        'PASSWORD': 'REDACTED',
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': '',
    }
}

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGGING_FILE_HANDLER = {
    'class': 'logging.FileHandler',
    'filename': os.path.join(BASE_DIR,
                             os.getenv('DJANGO_LOG_FILE', 'spool.log')),
    'formatter': 'verbose',
}


#####################################################################
# Email
#####################################################################
EMAIL_ENABLED = True

# email: dump emails in mailhog
# EMAIL_USE_TLS = False
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
# EMAIL_PORT = 1025

# email: send via gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'team@ascribe.io'
EMAIL_HOST_PASSWORD = os.environ['DJANGO_EMAIL_HOST_PASSWORD']
EMAIL_PORT = 587

COMPRESS_ENABLED = True
