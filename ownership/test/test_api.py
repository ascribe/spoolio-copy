# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

import pytest


pytestmark = pytest.mark.django_db


def test_list_zero(alice):
    from ..api import TransferEndpoint
    view = TransferEndpoint.as_view({'get': 'list'})
    factory = APIRequestFactory()
    url = reverse('api:ownership:ownershiptransfer-list')
    request = factory.get(url)
    force_authenticate(request, user=alice)
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 0


@pytest.mark.usefixtures('ownership_transfer')
def test_list_one(alice):
    from ..api import TransferEndpoint
    view = TransferEndpoint.as_view({'get': 'list'})
    factory = APIRequestFactory()
    url = reverse('api:ownership:ownershiptransfer-list')
    request = factory.get(url)
    force_authenticate(request, user=alice)
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1


def test_retrieve(ownership_transfer, alice):
    from ..api import TransferEndpoint
    view = TransferEndpoint.as_view({'get': 'retrieve'})
    factory = APIRequestFactory()
    pk = ownership_transfer.pk
    url = reverse('api:ownership:ownershiptransfer-detail', kwargs={'pk': pk})
    request = factory.get(url)
    force_authenticate(request, user=alice)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK
