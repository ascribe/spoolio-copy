# -*- coding: utf-8 -*-
"""
Regtest settings
"""

from __future__ import absolute_import

import os

from .local import *


# Local settings but with bitcoind running in regtest mode
# With this settings all transactions are automatically confirmed

BTC_ENABLED = os.environ.get('BTC_ENABLED', False)
BTC_SERVICE = 'regtest'
BTC_TESTNET = True
#CELERY_ALWAYS_EAGER = True

BTC_MAIN_WALLET = REGTEST_FEDERATION_ADDRESS
DJANGO_PYCOIN_ADMIN_PASS = REGTEST_FEDERATION_PASSWORD
BTC_REFILL_ADDRESS = REGTEST_REFILL_ADDRESS
BTC_REFILL_PASSWORD = REGTEST_REFILL_PASSWORD

BTC_USERNAME = REGTEST_USERNAME
BTC_PASSWORD = REGTEST_PASSWORD
BTC_HOST = REGTEST_HOST
BTC_PORT = REGTEST_PORT
