"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")


# from web import settings
# from repo.repositories import *
# settings.repo = {k: eval(r) for k, r in settings.repo.iteritems()}
# print 'Repositories loaded'

from django.core.wsgi import get_wsgi_application
from dj_static import Cling
# from django.conf import settings
# from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

application = Cling(get_wsgi_application())


# Bitcoin Initialization
from bitcoin.tasks import initialize_federation_wallet, initialize
from django.conf import settings

if settings.BTC_ENABLED:
    (initialize_federation_wallet.si() | initialize.si())()


#
# _django_app = Cling(get_wsgi_application())
# _websocket_app = uWSGIWebsocketServer()

# test uWSGI with low traffic:
# uwsgi --virtualenv /path/to/virtualenv --http :9090 --gevent 100 --http-websockets --module wsgi


# def application(environ, start_response):
# return _websocket_app(environ, start_response)
#     return _django_app(environ, start_response)
