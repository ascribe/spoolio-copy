from __future__ import absolute_import

from oauth2_provider.models import get_application_model

from ..api import create_token

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
    def create_token(application):
        return create_token(application, token='1234567890', valid_days=1)
