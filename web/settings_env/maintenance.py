# -*- coding: utf-8 -*-
"""
Maintenance settings
"""

from __future__ import absolute_import

import os

from .bitcoin_settings import *
from .common import *


#governs main settings. Local & staging are for devel. Staging & live are online. Live=production.
DEBUG = True
TEMPLATE_DEBUG = True

# Services
BTC_ENABLED = False
BTC_TESTNET = False
BTC_SERVICE = 'daemon'

#SSL: sslify
SSLIFY_ENABLE = False
SSLIFY_DISABLE = not SSLIFY_ENABLE

STRIPE_LIVE_ENABLED = False
if STRIPE_LIVE_ENABLED:
    assert SSLIFY_ENABLE == STRIPE_LIVE_ENABLED
# Host and Django settings
ASCRIBE_URL = 'http://localhost:' + os.environ['PORT'] + '/'
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
SITE_ID=1

###################
#  Services
###################
ZENCODER_API_KEY = os.environ['ZENCODER_API_KEY_TEST']

#Bitcoin
BTC_MAIN_WALLET = MAINNET_FEDERATION_ADDRESS
DJANGO_PYCOIN_ADMIN_PASS = MAINNET_FEDERATION_PASSWORD
BTC_REFILL_ADDRESS = MAINNET_REFILL_ADDRESS
BTC_REFILL_PASSWORD = MAINNET_REFILL_PASSWORD

BTC_USERNAME = MAINNET_USERNAME
BTC_PASSWORD = MAINNET_PASSWORD
BTC_HOST = MAINNET_HOST
BTC_PORT = MAINNET_PORT

# CELERY_ALWAYS_EAGER = True

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
DATABASES = {
#Use my local installation of postgresql. Works on both svn and git-heroku codebases.
'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'maintenance_db',
    'USER': 'mysite_user',
    'PASSWORD' : '123',
    'HOST': 'localhost',
    'PORT': '',
    }
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
