# -*- coding: utf-8 -*-
"""
Staging settings
"""

from __future__ import absolute_import

import os

from .bitcoin_settings import *
from .common import *


#governs main settings. Local & staging are for devel. Staging & live are online. Live=production.
DEBUG = False
TEMPLATE_DEBUG = False

# Services
BTC_ENABLED = True
BTC_SERVICE='daemon'

#SSL: sslify
SSLIFY_ENABLE = False
SSLIFY_DISABLE = not SSLIFY_ENABLE

STRIPE_LIVE_ENABLED = False
# Host and Django settings
ASCRIBE_URL = "https://www.ascribe.ninja/app/"
ASCRIBE_URL_NO_APP = "https://www.ascribe.ninja/"
ASCRIBE_URL_FRONTEND = ASCRIBE_URL
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Allow all host headers
ALLOWED_HOSTS = ['*']
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_NAME = 'csrftoken2'
CSRF_COOKIE_DOMAIN = '.ascribe.ninja'
CORS_ORIGIN_WHITELIST = (
    'ascribe.ninja',
    'staging.ascribe.io',
    'ascribe-jsapp.herokuapp.com',
    'giano-staging.herokuapp.com',
    'ci-ascribe.herokuapp.com',
    'cc-staging.ascribe.io',
    'localhost:8000',
    'localhost:3000',
)

CORS_ORIGIN_REGEX_WHITELIST = (
    '^(https?://)?(\w+\.)?localhost\.com:3000$',
    '^(https?://)?(\w+\.)?ascribe\.io$',
    '^(https?://)?(\w+\.)?ascribe\.ninja$',
    '^(https?://)?(\w+)?-staging.ascribe\.io$',
)

SITE_ID=1

###################
#  Services
###################
ZENCODER_API_KEY = os.environ['ZENCODER_API_KEY_TEST']
# PDF
ASCRIBE_PDF_URL = 'https://ascribepdf-staging.herokuapp.com'

#Bitcoin
#BTC_MAIN_WALLET = '12udvE3zmbQLhtSGZUqqAvGWSKDUCpbgoq'
#DJANGO_PYCOIN_ADMIN_PASS = 'REDACTED'

BTC_MAIN_WALLET = TESTNET_FEDERATION_ADDRESS
DJANGO_PYCOIN_ADMIN_PASS = TESTNET_FEDERATION_PASSWORD
BTC_REFILL_ADDRESS = TESTNET_REFILL_ADDRESS
BTC_REFILL_PASSWORD = TESTNET_REFILL_PASSWORD

BTC_USERNAME = TESTNET_USERNAME
BTC_PASSWORD = TESTNET_PASSWORD
BTC_HOST = TESTNET_HOST
BTC_PORT = TESTNET_PORT
BTC_TESTNET = True

#for amazon S3 storage
#http://stackoverflow.com/questions/10390244/how-to-set-up-a-django-project-with-django-storages-and-amazon-s3-but-with-diff
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = 'ascribe0'

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

COMPRESS_ENABLED = True
