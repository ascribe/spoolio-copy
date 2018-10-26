# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

import pytest


pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('djroot_user', 'bob_bitcoin_wallet', 's3_bucket')
def test_create_transfer(alice, bob, registered_edition_alice, alice_password):
    from ..api import TransferEndpoint
    from ..models import OwnershipTransfer
    data = {
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'transferee': bob.email,
        'password': alice_password,
    }
    view = TransferEndpoint.as_view({'post': 'create'})
    url = reverse('api:ownership:ownershiptransfer-list')
    factory = APIRequestFactory()
    request = factory.post(url, data, format='json')
    force_authenticate(request, user=alice)
    response = view(request)
    assert response.status_code == status.HTTP_201_CREATED
    assert 'transfer_pk'in response.data
    transfer_pk = response.data['transfer_pk']
    transfer = OwnershipTransfer.objects.get(pk=transfer_pk)
    assert transfer.edition.bitcoin_id == data['bitcoin_id']
    assert transfer.new_owner == bob


@pytest.mark.usefixtures('djroot_user', 'bob_bitcoin_wallet', 's3_bucket')
def test_try_create_unauthorized_transfer(carol,
                                          bob,
                                          registered_edition_alice,
                                          carol_password):
    from ..api import TransferEndpoint
    from ..models import OwnershipTransfer
    data = {
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'transferee': bob.email,
        'password': carol_password,
    }
    view = TransferEndpoint.as_view({'post': 'create'})
    url = reverse('api:ownership:ownershiptransfer-list')
    factory = APIRequestFactory()
    request = factory.post(url, data, format='json')
    force_authenticate(request, user=carol)
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not OwnershipTransfer.objects.filter(new_owner=bob)
