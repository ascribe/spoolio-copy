from __future__ import absolute_import

import json
from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from notifications.test.util import APIUtilEditionNotification
from ownership.test.util import (
    APIUtilTransfer,
    APIUtilConsign,
    APIUtilUnconsign,
    APIUtilContractAgreement,
)
from piece.test.util import APIUtilPiece
from s3.test.mocks import MockAwsTestCase
from users.test.util import APIUtilUsers


class TransferEndpointTest(MockAwsTestCase,
                           APIUtilTransfer,
                           APIUtilUsers,
                           APIUtilDigitalWork,
                           APIUtilThumbnail,
                           APIUtilPiece):
    fixtures = ['licenses.json']

    def _create_transfers(self):
        from ...models import OwnershipTransfer
        self.transfer_endpoint.create_transfer(self.web_user, self.other_user.email,
                                               self.editions_web[0].bitcoin_id, self.password)
        self.transfers_web = OwnershipTransfer.objects.get(prev_owner=self.web_user, new_owner=self.other_user)
        self.transfer_endpoint.create_transfer(self.other_user, self.web_user.email,
                                               self.editions_other[0].bitcoin_id, self.password)
        self.transfers_other = OwnershipTransfer.objects.get(prev_owner=self.other_user, new_owner=self.web_user)
        self.transfer_endpoint.create_transfer(self.other_user, self.oauth_user.email,
                                               self.editions_other[1].bitcoin_id, self.password)
        self.transfers_oauth = OwnershipTransfer.objects.get(prev_owner=self.other_user, new_owner=self.oauth_user)

    def setUp(self):
        super(TransferEndpointTest, self).setUp()
        self.transfer_endpoint = APIUtilTransfer()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.oauth_user = self.create_user('oauth-user@test.com')
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.factory = APIRequestFactory()

    def testListWeb(self):
        from ...api import TransferEndpoint
        from ...models import OwnershipTransfer
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        self._create_transfers()
        view = TransferEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/ownership/transfers/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        qs = OwnershipTransfer.objects.filter(Q(prev_owner=self.web_user) | Q(new_owner=self.web_user))

        serializer = OwnershipEditionSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'transfers': serializer.data}))
        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        for transfer in response.data['transfers']:
            self.assertIn('edition', transfer)
            self.assertNotIn('piece', transfer)

    def testRetrieveWeb(self):
        """
        Test that a user can retrieve registrations from himself.
        """
        from ...api import TransferEndpoint
        from ...models import OwnershipTransfer
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        self._create_transfers()
        view = TransferEndpoint.as_view({'get': 'retrieve'})
        url = '/api/ownership/transfers/{0}/'.format(self.transfers_web.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.transfers_web.id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        qs = OwnershipTransfer.objects.get(id=self.transfers_web.id)
        serializer = OwnershipEditionSerializer(qs, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'transfer': serializer.data}))
        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIn('edition', response.data['transfer'])
        self.assertNotIn('piece', response.data['transfer'])

    def testRetrieveOtherWeb(self):
        """
        Test that a user can't retrieve the ownership when he didnt participate if he knows the ID
        """
        from ...api import TransferEndpoint
        from ...models import OwnershipTransfer
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        self._create_transfers()
        view = TransferEndpoint.as_view({'get': 'retrieve'})
        url = '/api/ownership/transfers/{0}/'.format(self.transfers_other.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.transfers_other.id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        qs = OwnershipTransfer.objects.get(id=self.transfers_other.id)
        serializer = OwnershipEditionSerializer(qs, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'transfer': serializer.data}))
        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIn('edition', response.data['transfer'])
        self.assertNotIn('piece', response.data['transfer'])

        # transferred from web to other : access granted to other
        url = '/api/ownership/transfers/{0}/'.format(self.transfers_web.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.transfers_web.id)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        # transferred from other to oauth : access not granted to web
        url = '/api/ownership/transfers/{0}/'.format(self.transfers_web.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.transfers_oauth.id)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateWeb(self):
        """
        Test creation of a transfer
        """
        from ...api import TransferEndpoint
        from ...models import OwnershipTransfer
        # not yet created during setup ('local' i.s.o. 'test')
        data = {
            'bitcoin_id': self.editions_web[2].bitcoin_id,
            'transferee': 'other-user@test.com',
            'password': '0' * 10
        }
        view = TransferEndpoint.as_view({'post': 'create'})
        request = self.factory.post(
            '/api/ownership/transfers/', data, format='json')
        force_authenticate(request, user=self.web_user)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertIn('transfer_pk', response.data)
        transfer_pk = response.data['transfer_pk']
        transfer = OwnershipTransfer.objects.get(pk=transfer_pk)
        self.assertEqual(transfer.edition.bitcoin_id, data['bitcoin_id'])
        self.assertEqual(transfer.new_owner.email, data['transferee'])

        # TODO review what the goal of this test is ... the view & url are not
        # linked. ...
        view = TransferEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/pieces/', data)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_with_extra_data(self):
        """
        Test creation of a transfer
        """
        from ...api import TransferEndpoint
        from ...models import OwnershipTransfer
        # not yet created during setup ('local' i.s.o. 'test')
        data = {
            'bitcoin_id': self.editions_web[2].bitcoin_id,
            'transferee': 'other-user@test.com',
            'password': '0' * 10,
            'extra_data': {'price_value': '100', 'price_currency': 'EUR'}
        }
        view = TransferEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/transfers/', data, format='json')
        force_authenticate(request, user=self.web_user)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        response_data = response.data
        self.assertIn('success', response_data)
        self.assertTrue(response_data['success'])
        self.assertIn('transfer_pk', response_data)
        transfer_pk = response_data['transfer_pk']
        transfer = OwnershipTransfer.objects.get(pk=transfer_pk)
        self.assertDictEqual(transfer.extra_data, data['extra_data'])


class ConsignTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                         APIUtilPiece, APIUtilConsign, APIUtilUnconsign, APIUtilEditionNotification,
                         APIUtilContractAgreement):
    fixtures = ['licenses.json']

    def setUp(self):
        from ...models import Consignment
        super(ConsignTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

        # delete all loans
        Consignment.objects.all().delete()

    def test_web_user_list_consignments(self):
        from ...api import ConsignEndpoint
        from ...models import Consignment
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        consignment = Consignment.create(edition_alice, consignee=bob, owner=alice)
        consignment.save()

        url = reverse('api:ownership:consignment-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ConsignEndpoint.as_view({'get': 'list'})
        response = view(request)

        qs = Consignment.objects.filter(Q(prev_owner=alice) | Q(new_owner=bob))
        serializer = OwnershipEditionSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'consignments': serializer.data}))

        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        for consignment in response.data['consignments']:
            self.assertIn('edition', consignment)
            self.assertNotIn('piece', consignment)

    def test_web_user_retrieve_consignment(self):
        from ...api import ConsignEndpoint
        from ...models import Consignment
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        consignment = Consignment.create(edition_alice, consignee=bob, owner=alice)
        consignment.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:consignment-detail', kwargs={'pk': consignment.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ConsignEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=consignment.pk)

        serializer = OwnershipEditionSerializer(consignment, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        self.assertEqual(ordered_dict(response.data['consignment']), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertIn('edition', response.data['consignment'])
        self.assertNotIn('piece', response.data['consignment'])

    def testConsignRequestStatus(self):
        edition = self.editions_user1[0]

        # create consignment
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # retrieve edition notification
        response = self.retrieve_edition_notification(self.user2, edition.bitcoin_id)

        self.assertEqual(response.data['notification']['notification'],
                         [{'action': 'consign', 'action_str': 'Pending consign request', 'by': self.user1.username}])

    def testUnconsignRequestRequestStatus(self):
        edition = self.editions_user1[0]

        # create consignment - user1
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # accept consignment - user2
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # request_unconsign - user1
        self.request_unconsign(self.user1, edition.bitcoin_id)

        # retrieve edition notification
        response = self.retrieve_edition_notification(self.user2, edition.bitcoin_id)
        self.assertEqual(response.data['notification']['notification'],
                         [{'action': 'unconsign', 'action_str': 'Pending unconsign request',
                           'by': self.user1.username}])

    def test_consign_edition_with_contract(self):
        from ...models import Consignment
        edition = self.editions_user1[0]

        # create contract agreement
        contract_agreement = self.create_contractagreement(self.user2, self.user1)
        self.assertIsNone(contract_agreement.datetime_accepted)

        # create consign
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password, contract_agreement.id)
        consign = Consignment.objects.get(prev_owner=self.user1)

        self.assertEqual(consign.contract_agreement.id, contract_agreement.id)
        self.assertIsNotNone(consign.contract_agreement.datetime_accepted)

        # invalidate contract_agreement
        contract_agreement.datetime_deleted = datetime.utcnow()
        contract_agreement.save()

        response = self.create_consign(self.user1,
                                       self.user2.email,
                                       edition.bitcoin_id,
                                       self.password,
                                       contract_agreement.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UnConsignEndpointTest(TestCase):

    def test_web_user_list_unconsignments(self):
        from ...api import UnConsignEndpoint
        from ...models import UnConsignment, Consignment
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        consignment = Consignment.create(edition_alice, consignee=bob, owner=alice)
        consignment.save()
        unconsignment = UnConsignment.create(edition_alice, consignee=bob, owner=alice)
        unconsignment.save()

        url = reverse('api:ownership:unconsignment-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = UnConsignEndpoint.as_view({'get': 'list'})
        response = view(request)

        qs = UnConsignment.objects.filter(Q(prev_owner=bob) | Q(new_owner=alice))
        serializer = OwnershipEditionSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'unconsignments': serializer.data}))

        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        for unconsignment in response.data['unconsignments']:
            self.assertIn('edition', unconsignment)
            self.assertNotIn('piece', unconsignment)

    def test_web_user_retrieve_unconsignment(self):
        from ...api import UnConsignEndpoint
        from ...models import Consignment, UnConsignment
        from ...serializers import OwnershipEditionSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        consignment = Consignment.create(edition_alice, consignee=bob, owner=alice)
        consignment.save()
        unconsignment = UnConsignment.create(edition_alice, consignee=bob, owner=alice)
        unconsignment.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:unconsignment-detail', kwargs={'pk': unconsignment.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = UnConsignEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=unconsignment.pk)

        serializer = OwnershipEditionSerializer(unconsignment, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        self.assertEqual(ordered_dict(response.data['unconsignment']), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertIn('edition', response.data['unconsignment'])
        self.assertNotIn('piece', response.data['unconsignment'])
