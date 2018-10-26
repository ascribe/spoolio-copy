from __future__ import absolute_import

from django.utils.datetime_safe import datetime

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request

from piece.models import PieceFactory, Edition
from piece.api import EditionEndpoint, PieceEndpoint
from piece.tasks import register_editions
from ownership.models import License


class APIUtilPiece(object):
    factory = APIRequestFactory()

    # store the last request. It may be used in the tests
    # APIRequestFactory does not return a rest_framework request, only a django
    # http request https://github.com/tomchristie/django-rest-framework/issues/1928
    last_request = None

    @staticmethod
    def create_piece(user, digital_work, thumbnail,
                     title='title', artist_name='artist_name',
                     num_editions=2, consign=False):

        param = {
            'title': title,
            'artist_name': artist_name,
            'date_created': datetime.today().date(),
            'thumbnail': thumbnail,
            'digital_work': digital_work,
            'license': License.objects.get(code='default'),
            'num_editions': num_editions,
            'consign': consign
        }

        root_piece = PieceFactory.register(param, user)
        editions = Edition.objects.filter(owner=user, parent=root_piece)

        return root_piece, editions

    @staticmethod
    def create_consigned_registration(user, digital_work, thumbnail,
                         title='title', artist_name='artist_name',
                         num_editions=2):
        return APIUtilPiece.create_piece(user, digital_work, thumbnail,
                                         title=title, artist_name=artist_name,
                                         num_editions=num_editions, consign=True)

    @staticmethod
    def create_editions(user, piece, num_editions):
        if num_editions > 0:
            editions = register_editions(piece, user, num_editions).delay()
            return editions


    def delete_edition(self, user, edition_bitcoin_id):

        view = EditionEndpoint.as_view({'delete': 'delete'})
        request = self.factory.delete('/api/editions/')
        force_authenticate(request, user=user)

        response = view(request, pk=edition_bitcoin_id)
        return response

    def create_piece_web(self, user, title, artist_name, num_editions, digital_work_key,
                         date_created=datetime.today().date().year, thumbnail_file=None):
        data = {
            'title': title,
            'artist_name': artist_name,
            'num_editions': num_editions,
            'date_created': date_created,
            'digital_work_key': digital_work_key
        }
        if thumbnail_file:
            data['thumbnail_file'] = thumbnail_file

        view = PieceEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/pieces/', data)
        force_authenticate(request, user)

        response = view(request)
        self.last_request = Request(request)
        return response

    def list_pieces(self, user):
        view = PieceEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/pieces/')
        force_authenticate(request, user)

        response = view(request)
        self.last_request = Request(request)
        return response

    def list_piece_editions(self, user, pk):
        view = PieceEndpoint.as_view({'get': 'editions'})
        request = self.factory.get('/api/pieces/{}/editions/'.format(pk))
        force_authenticate(request, user)

        response = view(request, pk=pk)
        self.last_request = Request(request)
        return response

    def retrieve_edition(self, user, bitcoin_id):
        view = EditionEndpoint.as_view({'get': 'retrieve'})
        request = self.factory.get('/api/editions/{}/'.format(bitcoin_id))
        force_authenticate(request, user)

        response = view(request, pk=bitcoin_id)
        return response
