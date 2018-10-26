# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.http import HttpRequest

from rest_framework.request import Request

import pytest


class TestMarketSerializers(object):

    def test_market_piece_serializer_fields(self):
        from ..serializers import MarketPieceSerializer
        fields = MarketPieceSerializer.Meta.fields
        assert 'id' in fields
        assert 'title' in fields
        assert 'artist_name' in fields
        assert 'thumbnail' in fields
        assert 'bitcoin_id' in fields
        assert 'num_editions' in fields
        assert 'user_registered' in fields
        assert 'datetime_registered' in fields
        assert 'date_created' in fields
        assert 'license_type' in fields
        assert 'acl' in fields
        assert 'extra_data' in fields
        assert 'digital_work' in fields
        assert 'other_data' in fields
        assert 'loan_history' in fields
        assert 'private_note' in fields
        assert 'public_note' in fields
        assert 'notifications' in fields
        assert 'id' in fields
        assert 'title' in fields
        assert 'artist_name' in fields
        assert 'thumbnail' in fields
        assert 'bitcoin_id' in fields
        assert 'num_editions' in fields
        assert 'user_registered' in fields
        assert 'datetime_registered' in fields
        assert 'date_created' in fields
        assert 'license_type' in fields
        assert 'acl' in fields
        assert 'first_edition' in fields
        assert 'extra_data' in fields

    def test_market_detailed_edition_serializer_fields(self):
        from ..serializers import MarketDetailedEditionSerializer
        fields = MarketDetailedEditionSerializer.Meta.fields
        assert 'id' in fields
        assert 'title' in fields
        assert 'artist_name' in fields
        assert 'thumbnail' in fields
        assert 'bitcoin_id' in fields
        assert 'num_editions' in fields
        assert 'user_registered' in fields
        assert 'datetime_registered' in fields
        assert 'date_created' in fields
        assert 'license_type' in fields
        assert 'acl' in fields
        assert 'edition_number' in fields
        assert 'bitcoin_id' in fields
        assert 'parent' in fields
        assert 'notifications' in fields
        assert 'id' in fields
        assert 'title' in fields
        assert 'artist_name' in fields
        assert 'thumbnail' in fields
        assert 'bitcoin_id' in fields
        assert 'num_editions' in fields
        assert 'user_registered' in fields
        assert 'datetime_registered' in fields
        assert 'date_created' in fields
        assert 'license_type' in fields
        assert 'acl' in fields
        assert 'extra_data' in fields
        assert 'digital_work' in fields
        assert 'other_data' in fields
        assert 'loan_history' in fields
        assert 'private_note' in fields
        assert 'public_note' in fields
        assert 'notifications' in fields
        assert 'hash_as_address' in fields
        assert 'owner' in fields
        assert 'btc_owner_address_noprefix' in fields
        assert 'ownership_history' in fields
        assert 'consign_history' in fields
        assert 'coa' in fields
        assert 'status' in fields
        assert 'pending_new_owner' in fields
        assert 'consignee' in fields
        assert 'id' in fields
        assert 'title' in fields
        assert 'artist_name' in fields
        assert 'thumbnail' in fields
        assert 'bitcoin_id' in fields
        assert 'num_editions' in fields
        assert 'user_registered' in fields
        assert 'datetime_registered' in fields
        assert 'date_created' in fields
        assert 'license_type' in fields
        assert 'acl' in fields
        assert 'edition_number' in fields
        assert 'parent' in fields


class TestMarketBasicEditionSerializer(object):

    @pytest.mark.django_db
    def test_get_acl_for_anonymous_user(self, edition, whitelabel, monkeypatch):
        from ..serializers import MarketBasicEditionSerializer
        request = Request(
            HttpRequest(),
            parser_context={'kwargs': {'domain_pk': whitelabel.subdomain}},
        )
        monkeypatch.setattr(
            'piece.serializers.MinimalPieceSerializer.get_bitcoin_id',
            lambda x, y: 'bitcoin_id',
        )
        serializer = MarketBasicEditionSerializer(edition,
                                                  context={'request': request})
        assert serializer.data['acl'] == {}
