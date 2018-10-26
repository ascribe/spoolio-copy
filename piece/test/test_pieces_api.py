# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

import pytest


pytestmark = pytest.mark.django_db


def test_list_zero(alice):
    from ..api import PieceEndpoint
    view = PieceEndpoint.as_view({'get': 'list'})
    factory = APIRequestFactory()
    url = reverse('api:piece-list')
    request = factory.get(url)
    force_authenticate(request, alice)
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 0


def test_list_one(registered_piece_alice):
    from ..api import PieceEndpoint
    alice = registered_piece_alice.user_registered
    view = PieceEndpoint.as_view({'get': 'list'})
    factory = APIRequestFactory()
    url = reverse('api:piece-list')
    request = factory.get(url)
    force_authenticate(request, alice)
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['pieces']) == 1
    piece_data = response.data['pieces'][0]
    for attr in ('title', 'artist_name', 'num_editions', 'license_type',):
        assert piece_data[attr] == getattr(registered_piece_alice, attr), attr
    assert piece_data['user_registered'] == alice.username
    assert piece_data['date_created']
    assert piece_data['datetime_registered']
    assert 'first_edition' in piece_data
    assert 'thumbnail' in piece_data
    assert 'license_type' in piece_data


@pytest.mark.parametrize('pk_attr', ('pk', 'bitcoin_id'))
def test_retrieve_for_owner(registered_piece_alice, pk_attr):
    from ..api import PieceEndpoint
    from ..serializers import PieceSerializer
    alice = registered_piece_alice.user_registered
    pk = getattr(registered_piece_alice, pk_attr)
    view = PieceEndpoint.as_view({'get': 'retrieve'})
    url = reverse('api:piece-detail', kwargs={'pk': pk})
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=alice)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK
    serializer = PieceSerializer(registered_piece_alice,
                                 context={'request': request})
    assert response.data['piece'] == serializer.data


@pytest.mark.parametrize('pk_attr', ('pk', 'bitcoin_id'))
def test_retrieve_for_non_owner(registered_piece_alice, bob, pk_attr):
    from ..api import PieceEndpoint
    from ..serializers import PieceSerializer
    pk = getattr(registered_piece_alice, pk_attr)
    view = PieceEndpoint.as_view({'get': 'retrieve'})
    url = reverse('api:piece-detail', kwargs={'pk': pk})
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=bob)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK
    serializer = PieceSerializer(registered_piece_alice,
                                 context={'request': request})
    assert response.data['piece'] == serializer.data


# TODO verify why /api/blob/pieces not just /api/pieecs
@pytest.mark.parametrize('pk_attr', ('pk', 'bitcoin_id'))
def test_retrieve_via_blob(registered_piece_alice, pk_attr):
    from ..api import PieceEndpoint
    from ..serializers import PieceSerializer
    alice = registered_piece_alice.user_registered
    pk = getattr(registered_piece_alice, pk_attr)
    view = PieceEndpoint.as_view({'get': 'retrieve'})
    url = '/api/blob/pieces/{0}/'.format(pk)
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=alice)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK
    serializer = PieceSerializer(registered_piece_alice,
                                 context={'request': request})
    assert response.data['piece'] == serializer.data


@pytest.mark.parametrize('num_editions', (0, 1, 2))
@pytest.mark.usefixtures('license',
                         'djroot_bitcoin_wallet',
                         'alice_bitcoin_wallet')
def test_create(digital_work_alice, num_editions, thumbnail, monkeypatch):
    from ..api import PieceEndpoint
    from ..models import Piece
    monkeypatch.setattr(
        'blobs.models.DigitalWork.create_thumbnail', lambda s: thumbnail)
    alice = digital_work_alice.user
    title, artist_name, date_created = 'green', 'alice', 2000
    data = {
        'title': title,
        'artist_name': artist_name,
        'date_created': date_created,
        'digital_work_key': digital_work_alice.digital_work_file,
    }
    if num_editions:
        data['num_editions'] = num_editions
    view = PieceEndpoint.as_view({'post': 'create'})
    factory = APIRequestFactory()
    url = reverse('api:piece-list')
    request = factory.post(url, data)
    force_authenticate(request, alice)
    response = view(request)
    assert response.status_code == status.HTTP_201_CREATED
    piece_data = response.data['piece']
    assert piece_data['title'] == title
    assert piece_data['digital_work']['id'] == digital_work_alice.pk
    assert piece_data['artist_name'] == artist_name
    assert piece_data['date_created'] == '{}-01-01'.format(date_created)
    piece = Piece.objects.get(pk=piece_data['id'])
    assert piece.title == title
    assert piece.artist_name == artist_name
    assert piece.date_created.year == date_created
    assert piece.digital_work == digital_work_alice
    if num_editions:
        assert piece.num_editions == num_editions
    else:
        assert piece.num_editions == -1
    assert piece.piece_at_edition.count() == num_editions


@pytest.mark.usefixtures('license',
                         'djroot_bitcoin_wallet',
                         'alice_bitcoin_wallet')
def test_create_with_thumbnail(digital_work_alice, thumbnail_alice):
    from ..api import PieceEndpoint
    from ..models import Piece
    alice = digital_work_alice.user
    title, artist_name, date_created = 'green', 'alice', 2000
    data = {
        'title': title,
        'artist_name': artist_name,
        'date_created': date_created,
        'digital_work_key': digital_work_alice.digital_work_file,
        'thumbnail_file': thumbnail_alice.thumbnail_file,
    }
    view = PieceEndpoint.as_view({'post': 'create'})
    factory = APIRequestFactory()
    url = reverse('api:piece-list')
    request = factory.post(url, data)
    force_authenticate(request, alice)
    response = view(request)
    assert response.status_code == status.HTTP_201_CREATED
    piece_data = response.data['piece']
    assert piece_data['title'] == title
    assert piece_data['digital_work']['id'] == digital_work_alice.pk
    assert piece_data['artist_name'] == artist_name
    assert piece_data['date_created'] == '{}-01-01'.format(date_created)
    assert piece_data['thumbnail']['id'] == thumbnail_alice.pk
    piece = Piece.objects.get(pk=piece_data['id'])
    assert piece.title == title
    assert piece.artist_name == artist_name
    assert piece.date_created.year == date_created
    assert piece.digital_work == digital_work_alice
    assert piece.num_editions == -1
    assert piece.piece_at_edition.count() == 0
    assert piece.thumbnail.pk == thumbnail_alice.pk


def test_create_unauthenticated():
    from ..api import PieceEndpoint
    view = PieceEndpoint.as_view({'post': 'create'})
    factory = APIRequestFactory()
    url = reverse('api:piece-list')
    request = factory.post(url)
    response = view(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_editions_of_a_piece_by_pk(registered_edition_alice):
    from ..api import PieceEndpoint
    alice = registered_edition_alice.user_registered
    pk = registered_edition_alice.parent.pk
    view = PieceEndpoint.as_view({'get': 'editions'})
    factory = APIRequestFactory()
    url = reverse('api:piece-editions', kwargs={'pk': pk})
    request = factory.get(url)
    force_authenticate(request, alice)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['editions'][0]['id'] == registered_edition_alice.pk


def test_list_editions_of_a_piece_by_bitcoin_id(registered_edition_alice):
    from ..api import PieceEndpoint
    alice = registered_edition_alice.user_registered
    pk = registered_edition_alice.parent.bitcoin_id
    view = PieceEndpoint.as_view({'get': 'editions'})
    factory = APIRequestFactory()
    url = reverse('api:piece-editions', kwargs={'pk': pk})
    request = factory.get(url)
    force_authenticate(request, alice)
    response = view(request, pk=pk)
    assert response.status_code == status.HTTP_404_NOT_FOUND
