from __future__ import absolute_import

import datetime
from django.utils import timezone

from oauth2_provider.models import get_application_model, AccessToken

Application = get_application_model()


class APIUtilApplications(object):
    @staticmethod
    def create_application(user, name):
        app = Application(name=name, redirect_uris="", user=user,
                          client_type=Application.CLIENT_CONFIDENTIAL,
                          authorization_grant_type=Application.GRANT_PASSWORD)
        app.save()
        return app

    @staticmethod
    def create_token(user, application):
        expires = timezone.now() + datetime.timedelta(days=1)
        return AccessToken.objects.create(user=user, token='1234567890',
                                          application=application,
                                          expires=expires,
                                          scope='read write')
