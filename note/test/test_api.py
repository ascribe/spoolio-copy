# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize('view,privacy,element', (
    ('NoteEndpoint', 'private', 'editions'),
    ('PublicEditionNoteEndpoint', 'public', 'edition'),
    ('NotePieceEndpoint', 'private', 'pieces'),
    ('PublicPieceNoteEndpoint', 'public', 'pieces'),
))
def test_create_anonymous(view, privacy, element):
    from .. import api
    view = getattr(api, view).as_view({'post': 'create'})
    factory = APIRequestFactory()
    request = factory.post('/api/note/{}/{}/'.format(privacy, element))
    response = view(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_public_edition_note_by_squatter(bob, edition):
    from ..api import PublicEditionNoteEndpoint
    edition.bitcoin_path = 'dummy:path'
    edition.save()
    data = {'bitcoin_id': edition.bitcoin_id, 'note': 'note'}
    factory = APIRequestFactory()
    request = factory.post('/api/note/public/editions/', data=data)
    force_authenticate(request, user=bob)
    view = PublicEditionNoteEndpoint.as_view({'post': 'create'})
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_private_edition_note_by_squatter(bob, edition):
    from ..api import NoteEndpoint
    edition.bitcoin_path = 'dummy:path'
    edition.save()
    data = {'bitcoin_id': edition.bitcoin_id, 'note': 'note'}
    factory = APIRequestFactory()
    request = factory.post('/api/note/private/editions/', data=data)
    force_authenticate(request, user=bob)
    view = NoteEndpoint.as_view({'post': 'create'})
    response = view(request)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_public_piece_note_by_squatter(bob, piece):
    from ..api import PublicPieceNoteEndpoint
    data = {'id': piece.pk, 'note': 'note'}
    factory = APIRequestFactory()
    request = factory.post('/api/note/public/peices/', data=data)
    force_authenticate(request, user=bob)
    view = PublicPieceNoteEndpoint.as_view({'post': 'create'})
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_private_piece_note_by_squatter(bob, piece):
    from ..api import NotePieceEndpoint
    data = {'id': piece.pk, 'note': 'note'}
    factory = APIRequestFactory()
    request = factory.post('/api/note/private/peices/', data=data)
    force_authenticate(request, user=bob)
    view = NotePieceEndpoint.as_view({'post': 'create'})
    response = view(request)
    assert response.status_code == status.HTTP_201_CREATED
