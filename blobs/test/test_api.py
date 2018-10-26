# -*- coding:utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

import pytest


class TestThumbnailEndpoint(object):

    @pytest.mark.django_db
    def test_list(self, thumbnail):
        from ..api import ThumbnailEndpoint
        alice = thumbnail.user
        url = reverse('api:blob:thumbnail-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ThumbnailEndpoint.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['thumbnails']) == 1
        assert response.data['thumbnails'][0]['id'] == thumbnail.pk

    @pytest.mark.django_db
    def test_retrieve(self, thumbnail):
        from ..api import ThumbnailEndpoint
        pk = thumbnail.pk
        url = reverse('api:blob:thumbnail-detail', kwargs={'pk': pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=thumbnail.user)
        view = ThumbnailEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=pk)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['thumbnail']['id'] == thumbnail.pk

    @pytest.mark.django_db
    def test_create(self, alice, s3_bucket):
        from ..api import ThumbnailEndpoint
        from ..models import Thumbnail
        data = {'key': settings.THUMBNAIL_DEFAULT}
        url = reverse('api:blob:thumbnail-list')
        factory = APIRequestFactory()
        request = factory.post(url, data=data)
        force_authenticate(request, user=alice)
        view = ThumbnailEndpoint.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED
        thumbnail = Thumbnail.objects.get()
        assert thumbnail.thumbnail_file == settings.THUMBNAIL_DEFAULT

    @pytest.mark.django_db
    def test_delete_thumbnail_with_piece(self, piece_with_thumbnail):
        from ..api import ThumbnailEndpoint
        alice = piece_with_thumbnail.user_registered
        thumbnail = piece_with_thumbnail.thumbnail
        pk = thumbnail.pk
        url = reverse('api:blob:thumbnail-detail', kwargs={'pk': pk})
        factory = APIRequestFactory()
        request = factory.delete(url)
        force_authenticate(request, user=alice)
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=pk)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_delete_thumbnail(self, thumbnail):
        from ..api import ThumbnailEndpoint
        alice = thumbnail.user
        pk = thumbnail.pk
        url = reverse('api:blob:thumbnail-detail', kwargs={'pk': pk})
        factory = APIRequestFactory()
        request = factory.delete(url)
        force_authenticate(request, user=alice)
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=pk)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_delete_thumbnail_by_non_owner(self, thumbnail, bob):
        from ..api import ThumbnailEndpoint
        pk = thumbnail.pk
        url = reverse('api:blob:thumbnail-detail', kwargs={'pk': pk})
        factory = APIRequestFactory()
        request = factory.delete(url)
        force_authenticate(request, user=bob)
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=pk)
        assert response.status_code == status.HTTP_404_NOT_FOUND
