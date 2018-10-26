# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json

from django.core import mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

import pytest

@pytest.mark.django_db
@pytest.mark.usefixtures('djroot_user')
class TestShareEndpointTests(object):

    def test_web_user_list_shares(self, alice, bob, registered_edition_alice):
        from ..api import ShareEndpoint
        from ..models import Share
        from ..serializers import OwnershipEditionSerializer
        from util.util import ordered_dict

        share = Share.create(registered_edition_alice, sharee=bob)
        share.save()

        url = reverse('api:ownership:share-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ShareEndpoint.as_view({'get': 'list'})
        response = view(request)
        response.render()
        response_json = json.loads(response.content)

        qs = Share.objects.filter(Q(prev_owner=alice) | Q(new_owner=bob))
        serializer = OwnershipEditionSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'shares': serializer.data}))
        assert ordered_dict(response_json) == ordered_dict(response_db)
        assert response.status_code is status.HTTP_200_OK
        for share in response_json['shares']:
            assert 'edition' in share
            assert 'piece' not in share

    def test_web_user_retrieve_share(self, alice, bob, registered_edition_alice):
        from ..api import ShareEndpoint
        from ..models import Share
        from ..serializers import OwnershipEditionSerializer
        from util.util import ordered_dict

        share = Share.create(registered_edition_alice, sharee=bob)
        share.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:share-detail', kwargs={'pk': share.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ShareEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=share.pk)
        response.render()
        response_json = json.loads(response.content)

        serializer = OwnershipEditionSerializer(share, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        assert ordered_dict(response_json['share']) == ordered_dict(response_db)
        assert response.status_code is status.HTTP_200_OK
        assert 'edition' in response_json['share']
        assert 'piece' not in response_json['share']


@pytest.mark.django_db
class TestSharePieceEndpointTests(object):

    @pytest.mark.usefixtures('djroot_user')
    def test_web_user_list_shares_piece(self, alice, bob, registered_piece_alice):
        from ..api import SharePieceEndpoint
        from ..models import SharePiece
        from ..serializers import OwnershipPieceSerializer
        from util.util import ordered_dict

        share = SharePiece.create(registered_piece_alice, sharee=bob)
        share.save()

        url = reverse('api:ownership:sharepiece-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = SharePieceEndpoint.as_view({'get': 'list'})
        response = view(request)
        response.render()
        response_json = json.loads(response.content)

        qs = SharePiece.objects.filter(Q(prev_owner=alice) | Q(new_owner=bob))
        serializer = OwnershipPieceSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'shares': serializer.data}))
        assert ordered_dict(response_json) == ordered_dict(response_db)
        assert response.status_code is status.HTTP_200_OK
        for share in response_json['shares']:
            assert 'piece' in share
            assert 'edition' not in share

    @pytest.mark.usefixtures('djroot_user')
    def test_web_user_retrieve_share_piece(self, alice, bob, registered_piece_alice):
        from ..api import SharePieceEndpoint
        from ..models import SharePiece
        from ..serializers import OwnershipPieceSerializer
        from util.util import ordered_dict

        share = SharePiece.create(registered_piece_alice, sharee=bob)
        share.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:sharepiece-detail', kwargs={'pk': share.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = SharePieceEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=share.pk)
        response.render()
        response_json = json.loads(response.content)

        serializer = OwnershipPieceSerializer(share, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        assert ordered_dict(response_json['share']) == ordered_dict(response_db)
        assert response.status_code is status.HTTP_200_OK
        assert 'piece' in response_json['share']
        assert 'edition' not in response_json['share']

    def test_share_piece(self, alice, bob, piece):
        from ..api import SharePieceEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:sharepiece-list')
        data = {
            'share_emails': bob.email,
            'share_message': '',
            'piece_id': piece.pk,
        }
        request = factory.post(url, data=data)
        force_authenticate(request, user=alice)
        view = SharePieceEndpoint.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1

    def test_share_piece_with_oneself(self, alice, piece):
        from ..api import SharePieceEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:sharepiece-list')
        data = {
            'share_emails': alice.email,
            'share_message': '',
            'piece_id': piece.pk,
        }
        request = factory.post(url, data=data)
        force_authenticate(request, user=alice)
        view = SharePieceEndpoint.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
