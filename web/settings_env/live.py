# -*- coding: utf-8 -*-
"""
Live settings
"""

from __future__ import absolute_import

import os

from django.core.exceptions import ImproperlyConfigured

from .bitcoin_settings import *
from .common import *


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise ImproperlyConfigured(error_msg)


#governs main settings. Local & staging are for devel. Staging & live are online. Live=production.
DEBUG = False
TEMPLATE_DEBUG = False

# Services
BTC_ENABLED = True
BTC_SERVICE = 'daemon'

#SSL: sslify
SSLIFY_ENABLE = False # True
SSLIFY_DISABLE = not SSLIFY_ENABLE

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

STRIPE_LIVE_ENABLED = True
# assert SSLIFY_ENABLE == STRIPE_LIVE_ENABLED
# Host and Django settings
ASCRIBE_URL = "https://www.ascribe.io/app/"
ASCRIBE_URL_NO_APP = "https://www.ascribe.io/"
ASCRIBE_URL_FRONTEND = ASCRIBE_URL
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Allow headers with ascribe.io host
ALLOWED_HOSTS = ['*']
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_NAME = 'csrftoken2'
CSRF_COOKIE_DOMAIN = '.ascribe.io'
SITE_ID=1
###################
#  Services
###################
# Encoding
ZENCODER_API_KEY = os.environ['ZENCODER_API_KEY_LIVE']

# PDF
ASCRIBE_PDF_URL = 'https://ascribe-prod-pdf.herokuapp.com'

# Bitcoin
BTC_MAIN_WALLET = MAINNET_FEDERATION_ADDRESS
DJANGO_PYCOIN_ADMIN_PASS = MAINNET_FEDERATION_PASSWORD
BTC_REFILL_ADDRESS = MAINNET_REFILL_ADDRESS
BTC_REFILL_PASSWORD = MAINNET_REFILL_PASSWORD

BTC_USERNAME = MAINNET_USERNAME
BTC_PASSWORD = MAINNET_PASSWORD
BTC_HOST = MAINNET_HOST
BTC_PORT = MAINNET_PORT
BTC_TESTNET = False
#for amazon S3 storage
#http://stackoverflow.com/questions/10390244/how-to-set-up-a-django-project-with-django-storages-and-amazon-s3-but-with-diff
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = 'ascribe0'

CORS_ORIGIN_REGEX_WHITELIST = (
    '^(https?://)?(\w+\.)?ascribe\.io$',
)

###################
#  Database
###################
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
# https://devcenter.heroku.com/articles/heroku-postgresql
import dj_database_url
DATABASE_URL = os.environ['DATABASE_URL']
DATABASES = {
    ##from https://devcenter.heroku.com/articles/getting-started-with-django#start-a-django-app-inside-a-virtualenv
    'default' : dj_database_url.config(default=DATABASE_URL),
}


#####################################################################
# Email
#####################################################################
EMAIL_ENABLED = True

# email: send via gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'team@ascribe.io'
EMAIL_HOST_PASSWORD = os.environ['DJANGO_EMAIL_HOST_PASSWORD']
EMAIL_PORT = 587
