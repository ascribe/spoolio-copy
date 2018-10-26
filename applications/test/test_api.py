from __future__ import absolute_import

import pytest

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from oauth2_provider.models import AccessToken, get_application_model

pytestmark = pytest.mark.django_db
Application = get_application_model()
requestFactory = APIRequestFactory()


def test_create_token(oauth_application):
    """
    Test that access tokens are created for applications
    """
    from ..api import create_token
    token = create_token(oauth_application)
    token_model = AccessToken.objects.get(pk=token.pk)

    assert hasattr(token, 'token')
    assert token.token == token_model.token


def test_list_application(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can view his own applications
    """
    from ..api import ApplicationEndpoint
    url = '/api/applications/'
    request = requestFactory.get(url)
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'get': 'list'})
    response = view(request)
    applications_data = response.data['applications']

    assert response.status_code is status.HTTP_200_OK
    assert len(applications_data) == 1
    assert applications_data[0]['name'] == oauth_application.name
    assert applications_data[0]['bearer_token']['token'] == oauth_application_token.token


def test_retrieve_application(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can retrieve his own application
    """
    from ..api import ApplicationEndpoint
    url = '/api/applications/{0}/'.format(oauth_application.id)
    request = requestFactory.get(url)
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'get': 'retrieve'})
    response = view(request, pk=oauth_application.id)
    application_data = response.data['application']

    assert response.status_code is status.HTTP_200_OK
    assert application_data['name'] == oauth_application.name
    assert 'bearer_token' in application_data
    assert 'token' in application_data['bearer_token']


def test_create_application(oauth_user):
    """
    Test that a user can create applications.
    """
    from ..api import ApplicationEndpoint
    app_name = 'oauth-test-application'

    url = '/api/applications/'
    request = requestFactory.post(url, {
        'name': app_name
    })
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'post': 'create'})
    response = view(request)
    application_data = response.data['application']

    assert response.status_code is status.HTTP_201_CREATED
    assert application_data['name'] == app_name
    assert 'bearer_token' in application_data
    assert 'token' in application_data['bearer_token']


def test_refresh_application_token(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can refresh his application's token
    """
    from ..api import ApplicationEndpoint
    url = '/api/applications/'
    request = requestFactory.post(url, {
        'name': oauth_application.name
    })
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'post': 'refresh_token'})
    response = view(request)
    applications_data = response.data['applications']
    refresh_token_data = applications_data[0]

    assert response.status_code is status.HTTP_200_OK
    assert len(applications_data) == 1
    assert refresh_token_data['name'] == oauth_application.name
    assert refresh_token_data['bearer_token']['token'] != oauth_application_token.token
