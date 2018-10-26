# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

import pytest


pytestmark = pytest.mark.django_db


def test_list_editions(registered_edition_alice):
    from ..api import EditionEndpoint
    # TODO test response data editions
    alice = registered_edition_alice.user_registered
    url = reverse('api:edition-list')
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=alice)
    view = EditionEndpoint.as_view({'get': 'list'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert 'editions' in response.data
    edition_data = response.data['editions'][0]
    assert 'acl' in edition_data
    # TODO test response data editions


def test_retrieve_edition(registered_edition_alice):
    from ..api import EditionEndpoint
    alice = registered_edition_alice.user_registered
    url = reverse('api:edition-detail',
                  kwargs={'pk': registered_edition_alice.bitcoin_id})
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=alice)
    view = EditionEndpoint.as_view({'get': 'retrieve'})
    response = view(request, pk=registered_edition_alice.bitcoin_id)
    assert response.status_code == status.HTTP_200_OK
    assert 'edition' in response.data
