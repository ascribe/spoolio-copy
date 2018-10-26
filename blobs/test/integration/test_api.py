from __future__ import absolute_import

import json

from django.conf import settings
from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from ..api import DigitalWorkEndpoint, ThumbnailEndpoint, OtherDataEndpoint, ContractBlobEndpoint
from ..models import DigitalWork, Thumbnail, OtherData
from ..serializers import DigitalWorkSerializer, FileSerializer
from .util import APIUtilDigitalWork, APIUtilThumbnail, APIUtilOtherData, APIUtilContractBlobs
from piece.test.util import APIUtilPiece
from users.test.util import APIUtilUsers
from util.util import ordered_dict

from s3.test.mocks import MockAwsTestCase


# Test digitalwork creation
# Test listing digitalworks
# Test retrieving digitalworks
# Test deleting digitalworks
# Test deleting digitalworks with piece
class DigitalWorkEndpointTest(MockAwsTestCase, APIUtilUsers,
                              APIUtilDigitalWork, APIUtilPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        super(DigitalWorkEndpointTest, self).setUp()
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user, amount=10)
        self.digitalwork_other = self.create_digitalwork(self.other_user, amount=10)
        self.factory = APIRequestFactory()

    def testListWeb(self):
        """
        Test that a web user can list his digitalworks.
        He should not have access to the files of others in the db.
        """
        view = DigitalWorkEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/blob/digitalworks/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        # render the response so that we get the serialized json
        response.render()
        response_json = json.loads(response.content)['digitalworks']

        # get serialize the digitalwork form the db
        qs = DigitalWork.objects.filter(id__in=[d.id for d in self.digitalwork_web])
        serializer = DigitalWorkSerializer(qs, many=True)
        response_db = json.loads(json.dumps(serializer.data))
        self.assertEqual(ordered_dict(response_json), ordered_dict(response_db))

    def testRetrieveWeb(self):
        """
        Test that a user can only retrieve himself.
        """
        view = DigitalWorkEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/digitalworks/{0}/'.format(self.digitalwork_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.digitalwork_web[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = DigitalWork.objects.get(id=self.digitalwork_web[0].id)
        serializer = DigitalWorkSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'digitalwork': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveOtherWeb(self):
        """
        Test that a user can only retrieve digitalworks from himself.
        """
        view = DigitalWorkEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/digitalworks/{0}/'.format(self.digitalwork_other[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.digitalwork_other[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = DigitalWork.objects.get(id=self.digitalwork_other[0].id)
        serializer = DigitalWorkSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'digitalwork': serializer.data})
        self.assertEqual(response.content, serialized_db)

        url = '/api/blob/digitalworks/{0}/'.format(self.digitalwork_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.digitalwork_web[0].id)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateWeb(self):
        """
        Test creation of a digitalwork
        """
        # not yet created during setup ('local' i.s.o. 'test')
        key_test = 'test/giftest/ERuXtjY.gif'
        view = DigitalWorkEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/blob/digitalworks/', {
            'key': key_test,
        })
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        qs = DigitalWork.objects.get(digital_work_file=key_test, user=self.web_user)
        self.assertIsNotNone(qs)
        self.assertEqual(response.data['digitalwork']['url'], qs.url)
        self.assertEqual(len(DigitalWork.objects.filter(user=self.web_user)), len(self.digitalwork_web) + 1)
        request = self.factory.post('/api/blob/digitalworks/', {
            'key': key_test,
        })
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testDeleteDigitalWorkWithPiece(self):
        work = self.digitalwork_web[0]
        self.piece_web, self.editions_web = self.create_piece(self.web_user, work, None, num_editions=10)
        params = {'key': work.digital_work_file}
        view = DigitalWorkEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete('/api/blob/digitalworks/{0}/', params)
        force_authenticate(request, user=self.web_user)
        response = view(request, pk=work.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['errors']['non_field_errors'][0],
                         'Piece already registered, you cannot change the digital work')
        self.assertEqual(len(DigitalWork.objects.filter(user=self.web_user)), len(self.digitalwork_web))

    def testDeleteDigitalWorkWithoutPiece(self):
        work = self.digitalwork_web[0]
        self.assertEqual(DigitalWork.objects.get(id=work.id), work)
        params = {'key': work.digital_work_file}
        view = DigitalWorkEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete('/api/blob/digitalworks/{0}/', params)
        force_authenticate(request, user=self.other_user)

        response = view(request, pk=work.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(DigitalWork.objects.filter(user=self.web_user)), len(self.digitalwork_web))

        force_authenticate(request, user=self.web_user)
        response = view(request, pk=work.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(DigitalWork.objects.filter(user=self.web_user)), len(self.digitalwork_web) - 1)


# Test thumbnail creation
# Test listing thumbnails
# Test retrieving thumbnails
# Test deleting thumbnails
# Test deleting thumbnails with piece
class ThumbnailEndpointTest(TestCase, APIUtilUsers, APIUtilThumbnail,
                            APIUtilPiece, APIUtilDigitalWork):
    fixtures = ['licenses.json']

    def setUp(self):
        super(ThumbnailEndpointTest, self).setUp()
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digital_work_web = self.create_digitalwork(self.web_user, amount=1)
        self.thumbnail_web = self.create_thumbnail(self.web_user, amount=10)
        self.thumbnail_other = self.create_thumbnail(self.other_user, amount=10)
        self.factory = APIRequestFactory()

    def testListWeb(self):
        """
        Test that a web user can list his digitalworks.
        He should not have access to the files of others in the db.
        """
        view = ThumbnailEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/blob/thumbnails/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        # render the response so that we get the serialized json
        response.render()
        response_json = json.loads(response.content)['thumbnails']

        # get serialize the thumbnail form the db
        qs = Thumbnail.objects.filter(id__in=[d.id for d in self.thumbnail_web])
        serializer = FileSerializer(qs, many=True)
        response_db = json.loads(json.dumps(serializer.data))
        self.assertEqual(len(response_json), len(response_db))
        self.assertEqual(ordered_dict(response_json), ordered_dict(response_db))

    def testRetrieveWeb(self):
        """
        Test that a user can only retrieve himself.
        """
        view = ThumbnailEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/thumbnails/{0}/'.format(self.thumbnail_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.thumbnail_web[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = Thumbnail.objects.get(id=self.thumbnail_web[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'thumbnail': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveOtherWeb(self):
        """
        Test that a user can only retrieve thumbnails from himself.
        """
        view = ThumbnailEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/thumbnails/{0}/'.format(self.thumbnail_other[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.thumbnail_other[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = Thumbnail.objects.get(id=self.thumbnail_other[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'thumbnail': serializer.data})
        self.assertEqual(response.content, serialized_db)

        url = '/api/blob/thumbnails/{0}/'.format(self.thumbnail_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.thumbnail_web[0].id)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateWeb(self):
        # Here we cannot use the create_thumbnail default file
        key_test = 'test/giftest/ERuXtjY.gif'
        view = ThumbnailEndpoint.as_view({'post': 'create'})
        thumbnail_route = '/api/blob/thumbnails/'
        params = {'key': key_test}
        request = self.factory.post(thumbnail_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)

        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        th = Thumbnail.objects.get(thumbnail_file=key_test, user=self.web_user)
        self.assertIsNotNone(th)
        self.assertEqual(response.data['thumbnail']['url'], th.url)
        # test if all sizes are generated
        self.assertEqual(len(th.thumbnail_sizes), len(settings.THUMBNAIL_SIZES))

        request = self.factory.post(thumbnail_route, params)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testDeleteThumbnailWithPiece(self):
        key_test = 'test/giftest/ERuXtjY.gif'
        thumbnail_route = '/api/blob/thumbnails/{0}/'
        params = {'key': key_test}
        view = ThumbnailEndpoint.as_view({'post': 'create'})
        request = self.factory.post(thumbnail_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        response.render()

        th = Thumbnail.objects.get(thumbnail_file=key_test, user=self.web_user)
        self.digital_work_web = self.create_digitalwork(self.web_user, amount=1)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digital_work_web,
                                                              th, num_editions=10)
        params = {'key': th.thumbnail_file}
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete(thumbnail_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request, pk=th.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def testDeleteThumbnailWithoutPiece(self):
        key_test = 'test/giftest/ERuXtjY.gif'
        thumbnail_route = '/api/blob/thumbnails/{0}/'
        params = {'key': key_test}
        view = ThumbnailEndpoint.as_view({'post': 'create'})
        request = self.factory.post(thumbnail_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Thumbnail.objects.filter(user=self.web_user)), len(self.thumbnail_web) + 1)

        th = Thumbnail.objects.get(thumbnail_file=key_test, user=self.web_user)
        params = {'key': th.thumbnail_file}
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete(thumbnail_route, params)

        force_authenticate(request, user=self.other_user)
        response = view(request, pk=th.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Thumbnail.objects.filter(user=self.web_user)), len(self.thumbnail_web) + 1)

        force_authenticate(request, user=self.web_user)
        response = view(request, pk=th.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(Thumbnail.objects.filter(user=self.web_user)), len(self.thumbnail_web))


# Test otherdata creation
# Test listing otherdata
# Test retrieving otherdata
# Test deleting otherdata
class OtherdataEndpointTest(MockAwsTestCase, APIUtilUsers, APIUtilOtherData,
                            APIUtilPiece, APIUtilDigitalWork):
    fixtures = ['licenses.json']

    def setUp(self):
        super(OtherdataEndpointTest, self).setUp()
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digital_work_web = self.create_digitalwork(self.web_user, amount=1)
        self.otherdatas_web = self.create_otherdata(self.web_user, amount=10)
        self.otherdatas_other = self.create_otherdata(self.other_user, amount=10)
        self.factory = APIRequestFactory()

    def testListWeb(self):
        """
        Test that a web user can list his digitalworks.
        He should not have access to the files of others in the db.
        """
        view = OtherDataEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/blob/otherdatas/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        # render the response so that we get the serialized json
        response_json = response.data['otherdatas']

        # get serialize the otherdata form the db
        qs = OtherData.objects.filter(id__in=[d.id for d in self.otherdatas_web])
        serializer = FileSerializer(qs, many=True)
        response_db = json.loads(json.dumps(serializer.data))
        self.assertEqual(len(response_json), len(response_db))
        self.assertEqual(ordered_dict(response_json), ordered_dict(response_db))

    def testRetrieveWeb(self):
        """
        Test that a user can only retrieve himself.
        """
        view = OtherDataEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/otherdatas/{0}/'.format(self.otherdatas_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.otherdatas_web[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = OtherData.objects.get(id=self.otherdatas_web[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'otherdata': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveOtherWeb(self):
        """
        Test that a user can only retrieve Otherdata from himself.
        """
        view = OtherDataEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/otherdatas/{0}/'.format(self.otherdatas_other[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.otherdatas_other[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = OtherData.objects.get(id=self.otherdatas_other[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'otherdata': serializer.data})
        self.assertEqual(response.content, serialized_db)

        url = '/api/blob/otherdatas/{0}/'.format(self.otherdatas_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.otherdatas_web[0].id)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateWeb(self):
        # Here we cannot use the create_otherdata default file
        key_test = 'test/giftest/ERuXtjY.gif'
        piece, editions = self.create_piece(self.web_user, self.digital_work_web, None)
        view = OtherDataEndpoint.as_view({'post': 'create'})
        otherdata_route = '/api/blob/otherdatas/'
        params = {'key': key_test, 'piece_id': piece.id}
        request = self.factory.post(otherdata_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)

        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        qs = OtherData.objects.get(other_data_file=key_test, user=self.web_user)
        self.assertIsNotNone(qs)
        self.assertEqual(response.data['otherdata']['url'], qs.url)

        # other_user cannot attach to piece of web_user
        force_authenticate(request, user=self.other_user)
        response = view(request)
        response.render()

        self.assertIs(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['errors']['non_field_errors'][0],
                         u"You don't have the appropriate rights to edit this field")

        request = self.factory.post(otherdata_route, params)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testDeleteOtherData(self):
        key_test = 'test/giftest/ERuXtjY.gif'
        piece, editions = self.create_piece(self.web_user, self.digital_work_web, None)
        view = OtherDataEndpoint.as_view({'post': 'create'})
        otherdata_route = '/api/blob/otherdatas/'
        params = {'key': key_test, 'piece_id': piece.id}
        request = self.factory.post(otherdata_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response.render()

        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        otherdata = OtherData.objects.get(other_data_file=key_test, user=self.web_user)
        params = {'key': otherdata.other_data_file}
        view = OtherDataEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete(otherdata_route, params)

        force_authenticate(request, user=self.other_user)
        response = view(request, pk=otherdata.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(OtherData.objects.filter(user=self.web_user)), len(self.otherdatas_web) + 1)

        force_authenticate(request, user=self.web_user)
        response = view(request, pk=otherdata.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(OtherData.objects.filter(user=self.web_user)), len(self.otherdatas_web))

    def testFineuploaderSession(self):
        view = OtherDataEndpoint.as_view({'get': 'fineuploader_session'})
        otherdata_route = '/api/blob/otherdatas/?pk={}'.format(self.otherdatas_web[0].pk)
        request = self.factory.get(otherdata_route)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['uuid'], self.otherdatas_web[0].pk)

        otherdata_route = '/api/blob/otherdatas/?pk={},{}'.format(self.otherdatas_web[0].pk,
                                                                  self.otherdatas_web[1].pk)
        request = self.factory.get(otherdata_route)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertIn(response_data[0]['uuid'], [self.otherdatas_web[0].pk, self.otherdatas_web[1].pk])
        self.assertIn(response_data[1]['uuid'], [self.otherdatas_web[0].pk, self.otherdatas_web[1].pk])
        self.assertNotEqual(response_data[0]['uuid'], response_data[1]['uuid'])


# Test contractblobs creation
# Test listing contractblobs
# Test retrieving contractblobs
# Test deleting contractblobs
class ContractBlobEndpointTest(MockAwsTestCase, APIUtilUsers,
                               APIUtilContractBlobs, APIUtilPiece):
    def setUp(self):
        super(ContractBlobEndpointTest, self).setUp()
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.contracts_web = self.create_contract(self.web_user, amount=10)
        self.contracts_other = self.create_contract(self.other_user, amount=10)
        self.factory = APIRequestFactory()

    def testListWeb(self):
        """
        Test that a web user can list his digitalworks.
        He should not have access to the files of others in the db.
        """
        view = ContractBlobEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/blob/contracts/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)
        # render the response so that we get the serialized json
        response_json = response.data['contractblobs']

        # get serialize the contract form the db
        qs = OtherData.objects.filter(id__in=[d.id for d in self.contracts_web])
        serializer = FileSerializer(qs, many=True)
        response_db = json.loads(json.dumps(serializer.data))
        self.assertEqual(len(response_json), len(response_db))
        self.assertEqual(ordered_dict(response_json), ordered_dict(response_db))

    def testRetrieveWeb(self):
        """
        Test that a user can only retrieve himself.
        """
        view = ContractBlobEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/contracts/{0}/'.format(self.contracts_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.contracts_web[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = OtherData.objects.get(id=self.contracts_web[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'contractblob': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveOtherWeb(self):
        """
        Test that a user can only retrieve Contracts from himself.
        """
        view = ContractBlobEndpoint.as_view({'get': 'retrieve'})
        url = '/api/blob/contracts/{0}/'.format(self.contracts_other[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.contracts_other[0].id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = OtherData.objects.get(id=self.contracts_other[0].id)
        serializer = FileSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True, 'contractblob': serializer.data})
        self.assertEqual(response.content, serialized_db)

        url = '/api/blob/contracts/{0}/'.format(self.contracts_web[0].id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.contracts_web[0].id)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateWeb(self):
        # Here we cannot use the create_contract default file
        key_test = 'test/giftest/ERuXtjY.gif'
        params = {'key': key_test}

        contract_route = '/api/blob/contracts/'
        view = ContractBlobEndpoint.as_view({'post': 'create'})
        request = self.factory.post(contract_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)

        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        qs = OtherData.objects.get(other_data_file=key_test, user=self.web_user)
        self.assertIsNotNone(qs)
        self.assertEqual(response.data['contractblob']['url'], qs.url)

        request = self.factory.post(contract_route, params)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testDeleteContract(self):
        key_test = 'test/giftest/ERuXtjY.gif'
        view = ContractBlobEndpoint.as_view({'post': 'create'})
        contract_route = '/api/blob/contracts/'
        params = {'key': key_test}
        request = self.factory.post(contract_route, params)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response.render()

        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        contract = OtherData.objects.get(other_data_file=key_test, user=self.web_user)
        params = {'key': contract.other_data_file}
        view = ContractBlobEndpoint.as_view({'delete': 'destroy'})
        request = self.factory.delete(contract_route, params)

        force_authenticate(request, user=self.other_user)
        response = view(request, pk=contract.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(OtherData.objects.filter(user=self.web_user)), len(self.contracts_web) + 1)

        force_authenticate(request, user=self.web_user)
        response = view(request, pk=contract.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(OtherData.objects.filter(user=self.web_user)), len(self.contracts_web))

    def testFineuploaderSession(self):
        view = ContractBlobEndpoint.as_view({'get': 'fineuploader_session'})
        contract_route = '/api/blob/contracts/?pk={}'.format(self.contracts_web[0].pk)
        request = self.factory.get(contract_route)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['uuid'], self.contracts_web[0].pk)

        contract_route = '/api/blob/contracts/?pk={},{}'.format(self.contracts_web[0].pk,
                                                                self.contracts_web[1].pk)
        request = self.factory.get(contract_route)
        force_authenticate(request, user=self.web_user)
        response = view(request)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertIn(response_data[0]['uuid'], [self.contracts_web[0].pk, self.contracts_web[1].pk])
        self.assertIn(response_data[1]['uuid'], [self.contracts_web[0].pk, self.contracts_web[1].pk])
        self.assertNotEqual(response_data[0]['uuid'], response_data[1]['uuid'])
