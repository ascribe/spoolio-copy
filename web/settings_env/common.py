# -*- coding: utf-8 -*-
"""
Django common (aka base) settings for spool project.
More info: https://docs.djangoproject.com/en/1.6/topics/settings/
Full list of settings: https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from __future__ import absolute_import


#####################################################################
# Email
#####################################################################

# email: address we send from
ASCRIBE_EMAIL = 'ascribe <team@ascribe.io>'

# email: signature
EMAIL_SIGNATURE = """\
%(ascribe_team)s\n\n----
ascribe GmbH
Wichertstr. 17, 10439 Berlin
Managing Director: Bruce Pon
Registered in Berlin HRB 160856B
info@ascribe.io
"""

# email: send via gmail
EMAIL_USE_TLS = True

# whitelist of emails allowed in development
EMAIL_WHITELIST = [
    'ascribe.io',
    'mailinator.com',
    'test.com',  # for unittests
]

DEFAULT_FROM_EMAIL = ASCRIBE_EMAIL
EMAIL_DEV_ALERT = 'devel@ascribe.io'

# TODO HACK ALERT! This is for a hack. Will be changed/moved asap.
PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME = '2016-01-05T23:00:00'
PORTFOLIO_REVIEW_ROUND_TIMEFORMAT = '%Y-%m-%dT%H:%M:%S'
