from rest_framework.test import APIRequestFactory, force_authenticate

from note.api import NoteEndpoint, NotePieceEndpoint
from note.api import PublicEditionNoteEndpoint, PublicPieceNoteEndpoint


class APINoteUtil(object):
    factory = APIRequestFactory()

    def create_edition_private_note(self, user, bitcoin_id, note):
        data = {'bitcoin_id': bitcoin_id, 'note': note}
        view = NoteEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/note/private/editions/', data)
        force_authenticate(request, user)

        response = view(request)
        return response

    def create_edition_public_note(self, user, bitcoin_id, note):
        data = {'bitcoin_id': bitcoin_id, 'note': note}
        view = PublicEditionNoteEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/note/public/editions/', data)
        force_authenticate(request, user)

        response = view(request)
        return response

    def create_piece_private_note(self, user, piece_id, note):
        data = {'id': piece_id, 'note': note}
        view = NotePieceEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/note/private/pieces/', data)
        force_authenticate(request, user)

        response = view(request)
        return response

    def create_piece_public_note(self, user, piece_id, note):
        data = {'id': piece_id, 'note': note}
        view = PublicPieceNoteEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/note/public/piece/', data)
        force_authenticate(request, user)

        response = view(request)
        return response

    def list_edition_private_note(self, user):
        view = NoteEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/note/private/editions/')
        force_authenticate(request, user)

        response = view(request)
        return response

    def list_edition_public_note(self, user):
        view = PublicEditionNoteEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/note/public/editions/')
        force_authenticate(request, user)

        response = view(request)
        return response

    def list_piece_private_note(self, user):
        view = NotePieceEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/note/private/pieces/')
        force_authenticate(request, user)

        response = view(request)
        return response

    def list_piece_public_note(self, user):
        view = PublicPieceNoteEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/note/public/pieces/')
        force_authenticate(request, user)

        response = view(request)
        return response
