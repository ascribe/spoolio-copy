# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.core.urlresolvers import reverse

import pytest
from oauth2_provider.models import get_application_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

pytestmark = pytest.mark.django_db
Application = get_application_model()


def test_list_application(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can view his own applications
    """
    from ..api import ApplicationEndpoint
    url = reverse('api:applications:application-list')
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'get': 'list'})
    response = view(request)
    applications_data = response.data['applications']

    assert response.status_code == status.HTTP_200_OK
    assert len(applications_data) == 1
    assert applications_data[0]['name'] == oauth_application.name
    assert applications_data[0]['bearer_token']['token'] == oauth_application_token.token


def test_retrieve_application(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can retrieve his own application
    """
    from ..api import ApplicationEndpoint
    url = reverse('api:applications:application-detail',
                  kwargs={'pk': oauth_application.id})
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'get': 'retrieve'})
    response = view(request, pk=oauth_application.id)
    application_data = response.data['application']

    assert response.status_code == status.HTTP_200_OK
    assert application_data['name'] == oauth_application.name
    assert 'bearer_token' in application_data
    assert 'token' in application_data['bearer_token']


def test_create_application(oauth_user):
    """
    Test that a user can create applications.
    """
    from ..api import ApplicationEndpoint
    app_name = 'oauth-test-application'

    url = reverse('api:applications:application-list')
    factory = APIRequestFactory()
    request = factory.post(url, {'name': app_name})
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'post': 'create'})
    response = view(request)
    application_data = response.data['application']

    assert response.status_code == status.HTTP_201_CREATED
    assert application_data['name'] == app_name
    assert 'bearer_token' in application_data
    assert 'token' in application_data['bearer_token']


def test_refresh_application_token(oauth_user, oauth_application, oauth_application_token):
    """
    Test that a user can refresh his application's token
    """
    from ..api import ApplicationEndpoint
    url = reverse('api:applications:application-list')
    factory = APIRequestFactory()
    request = factory.post(url, {'name': oauth_application.name})
    force_authenticate(request, user=oauth_user)

    view = ApplicationEndpoint.as_view({'post': 'refresh_token'})
    response = view(request)
    applications_data = response.data['applications']
    refresh_token_data = applications_data[0]

    assert response.status_code == status.HTTP_200_OK
    assert len(applications_data) == 1
    assert refresh_token_data['name'] == oauth_application.name
    assert refresh_token_data['bearer_token']['token'] != oauth_application_token.token
