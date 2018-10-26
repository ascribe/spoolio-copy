import hashlib
import logging
import random
import urlparse
from string import digits, ascii_uppercase, ascii_lowercase

import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as django_reverse
from django.http import HttpResponseRedirect

from rest_framework.reverse import reverse


logger = logging.getLogger(__name__)


def reverse_url(viewname, urlconf=None, args=None, kwargs=None, prefix=None, current_app=None):
    return settings.ASCRIBE_URL_NO_APP[:-1] \
           + django_reverse(viewname, urlconf, args, kwargs, prefix, current_app)


# ====================================================
# admin
def mainAdminUser():
    # TODO filter by is_superuser, and other criteria instead, e.g.:
    # return User.objects.get(email='djangoroot@ascribe.io')
    # return User.objects.filter(is_superuser=True).order_by('date_joined')[0]
    return User.objects.all().order_by('date_joined')[0]


def mainAdminPassword():
    """@return -- main admin password *for pycoin* """
    return settings.DJANGO_PYCOIN_ADMIN_PASS


def insert_or_change_subdomain(url, subdomain):
    parsed_url = urlparse.urlparse(url)
    port = ':' + str(parsed_url.port) if parsed_url.port else ''
    host = parsed_url.hostname.split('.')
    new_host = [subdomain] + host if len(host) == 2 else [subdomain] + host[1:]
    new_host = '.'.join(new_host) + port
    return urlparse.urlunsplit([parsed_url.scheme,
                                new_host,
                                parsed_url.path,
                                parsed_url.query,
                                parsed_url.params])


def extract_subdomain(url):
    hostname = urlparse.urlparse(url).hostname.split('.')
    return hostname[0] if len(hostname) == 3 else 'www'


# ==============================================================
def hash_string(str):
    md5 = hashlib.md5()
    md5.update(str)
    return md5.hexdigest()


# ====================================================
# btc prefix
def remove_btc_prefix(bitcoin_address):
    if ':' in bitcoin_address:
        return bitcoin_address.split(':')[1]
    else:
        return bitcoin_address


# ====================================================
def randomStr(n, chars=None):
    if chars is None:
        chars = digits + ascii_uppercase + ascii_lowercase
    return ''.join([random.choice(chars) for i in xrange(n)])


# ====================================================
def ordered_dict(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered_dict(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered_dict(x) for x in obj)
    else:
        return obj


def send_mail(subject, message, email_to, html_message=None):
    blacklist = False

    if settings.DEPLOYMENT != 'live' and not settings.TESTING:
        blacklist = True
        for pattern in settings.EMAIL_WHITELIST:
            if email_to.lower().find(pattern) != -1:
                blacklist = False
                break

    if not blacklist:
        email_from = settings.ASCRIBE_EMAIL
        # main work
        from django.core.mail import send_mail
        send_mail(subject, message, email_from, [email_to],
                  html_message=html_message, fail_silently=False)
    else:
        logger.warn(
            'Email %s is blacklisted on non-live environments', email_to)


def warn_ascribe_devel(subject, message):
    if settings.EMAIL_ENABLED and settings.DEPLOYMENT == 'live':
        send_mail(subject, message, settings.EMAIL_DEV_ALERT)
