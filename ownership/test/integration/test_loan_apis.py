# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import json
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from notifications.test.util import APIUtilEditionNotification
from ownership.test.util import APIUtilLoanPiece, APIUtilLoanEdition
from piece.test.util import APIUtilPiece
from s3.test.mocks import MockAwsTestCase
from users.test.util import APIUtilUsers


class LoanEndpointTest(TestCase):
    @unittest.skip('until Loan.edition is None issue (AD-881) is fixed')
    def test_get_loans_non_authenticated(self):
        from ...api import LoanEndpoint
        from ...models import Loan
        from blobs.models import DigitalWork
        from piece.models import Piece

        alice = User.objects.create(email='alice@xyz.ct')
        digital_work = DigitalWork.objects.create()
        piece = Piece.objects.create(date_created=date.today(),
                                     user_registered=alice,
                                     digital_work=digital_work)
        Loan.objects.create(piece=piece)

        url = reverse('api:ownership:loan-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        view = LoanEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    @unittest.skip('until Loan.edition is None issue (AD-881) is fixed')
    def test_get_loans_authenticated(self):
        from ...api import LoanEndpoint
        from ...models import Loan
        from blobs.models import DigitalWork
        from piece.models import Piece
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        digital_work = DigitalWork.objects.create()
        piece_by_alice = Piece.objects.create(date_created=date.today(),
                                              user_registered=alice,
                                              digital_work=digital_work)
        piece_by_bob = Piece.objects.create(date_created=date.today(),
                                            user_registered=bob,
                                            digital_work=digital_work)
        loan_by_alice = Loan.objects.create(
            piece=piece_by_alice, prev_owner=alice, type='Loan')
        Loan.objects.create(piece=piece_by_bob, prev_owner=bob, type='Loan')
        url = reverse('api:ownership:loan-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = LoanEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['loans'][0]['id'], loan_by_alice.pk)


class WebLoanPieceTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork,
                       APIUtilThumbnail, APIUtilPiece, APIUtilLoanPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        super(WebLoanPieceTest, self).setUp()
        # TODO the admin user needs to be created for bitcoin related reasons
        self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

    def test_web_user_list_loans_piece(self):
        from ...api import LoanPieceEndpoint
        from ...models import LoanPiece
        from ...serializers import LoanPieceSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_piece_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        piece_alice = _registered_piece_alice()
        loan = LoanPiece.create(piece_alice, loanee=bob, owner=alice)
        loan.save()

        url = reverse('api:ownership:loanpiece-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = LoanPieceEndpoint.as_view({'get': 'list'})
        response = view(request)

        qs = LoanPiece.objects.filter(Q(prev_owner=alice) | Q(new_owner=bob))
        serializer = LoanPieceSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'loans': serializer.data}))
        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        for loan in response.data['loans']:
            self.assertIn('piece', loan)
            self.assertNotIn('edition', loan)

    def test_web_user_retrieve_loan_piece(self):
        from ...api import LoanPieceEndpoint
        from ...models import LoanPiece
        from ...serializers import LoanPieceSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_piece_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        piece_alice = _registered_piece_alice()
        loan = LoanPiece.create(piece_alice, loanee=bob, owner=alice)
        loan.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:loan-detail', kwargs={'pk': loan.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = LoanPieceEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=loan.pk)

        serializer = LoanPieceSerializer(loan, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        self.assertEqual(ordered_dict(response.data['loan']), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertIn('piece', response.data['loan'])
        self.assertNotIn('edition', response.data['loan'])

    def test_create_loan_piece(self):
        from ...api import LoanPieceEndpoint
        from ...models import LoanPiece
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_piece_alice

        password = 'secret-alice'
        _djroot_user()
        alice = _alice()
        bob = _bob()
        piece_alice = _registered_piece_alice()
        data = {
            'loanee': bob.email,
            'piece_id': piece_alice.pk,
            'startdate': datetime.utcnow().date(),
            'enddate': datetime.utcnow().date() + timedelta(days=1),
            'password': password,
            'terms': True
        }
        view = LoanPieceEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        url = reverse('api:ownership:loanpiece-list')
        request = factory.post(url, data)
        force_authenticate(request, user=alice)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check that the loan exists
        loans = LoanPiece.objects.filter(piece=piece_alice)
        self.assertEqual(len(loans), 1)
        loan = loans[0]

        # check owners
        self.assertEqual(loan.prev_owner, alice)
        self.assertEqual(loan.new_owner, bob)

        # check the status is None (meaning unconfirmed)
        self.assertIsNone(loan.status)

        self.assertIn('loan', response.data)
        self.assertIn('piece', response.data['loan'])

    def test_loan_piece_not_owned(self):
        from ...api import LoanPieceEndpoint
        from ...models import LoanPiece
        password = '0' * 10
        alice = self.create_user('alice@test.com')
        bob = self.create_user('bob@test.com')
        digitalwok_alice = self.create_digitalwork(alice)
        thumbnail_alice = self.create_thumbnail(alice)
        piece_alice, _ = self.create_piece(
            alice,
            digitalwok_alice,
            thumbnail_alice,
            num_editions=2,
        )
        data = {
            'loanee': alice.email,
            'piece_id': piece_alice.pk,
            'startdate': datetime.utcnow().date(),
            'enddate': datetime.utcnow().date() + timedelta(days=1),
            'password': password,
            'terms': True
        }
        view = LoanPieceEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        url = reverse('api:ownership:loanpiece-list')
        request = factory.post(url, data)
        force_authenticate(request, user=bob)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(LoanPiece.objects.filter(piece=piece_alice).exists())

    def test_deny_loan_piece(self):
        from ...models import LoanPiece

        password = '0' * 10
        user1 = self.create_user('user1@test.com')
        user2 = self.create_user('user2@test.com')
        digitalwok_user1 = self.create_digitalwork(user1)
        thumbnail_user1 = self.create_thumbnail(user1)
        piece_user1, _ = self.create_piece(
            user1,
            digitalwok_user1,
            thumbnail_user1,
            num_editions=2,
        )

        self.create_loan_piece(
            user1,
            user2.email,
            piece_user1.pk,
            startdate=datetime.utcnow().date(),
            enddate=datetime.utcnow().date() + timedelta(days=1),
            password=password,
        )
        response = self.deny_loan_piece(user2, piece_user1.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        loan = LoanPiece.objects.get(piece=piece_user1)
        # check status is 0 (denied)
        self.assertEqual(loan.status, 0)

    def test_loan_history_with_contract(self):
        from blobs.models import OtherData
        from ...models import LoanPiece, Contract, ContractAgreement
        password = '0' * 10
        user1 = self.create_user('user1@test.com')
        user2 = self.create_user('user2@test.com')
        digitalwok_user1 = self.create_digitalwork(user1)
        thumbnail_user1 = self.create_thumbnail(user1)
        piece_user1, _ = self.create_piece(
            user1,
            digitalwok_user1,
            thumbnail_user1,
            num_editions=2,
        )

        # create contract
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=user2, blob=blob, name='test-contract')

        # create contract agreement
        contract_agreement = ContractAgreement.objects.create(signee=user1, contract=contract)
        # accept contract agreement
        contract_agreement.datetime_accepted = datetime.utcnow()

        # create loan
        self.create_loan_piece(user1, user2.email, piece_user1.pk,
                               startdate=datetime.utcnow().date(),
                               enddate=datetime.utcnow().date() + timedelta(days=1),
                               password=password,
                               contract_agreement_id=contract_agreement.pk)

        # retrieve loan
        # TODO why?
        LoanPiece.objects.get(prev_owner=user1)
        loan_history = piece_user1.loan_history

        self.assertEqual(loan_history[0][2], contract.blob.url_safe)

    def test_loan_history_without_contract(self):
        from ...models import LoanPiece
        password = '0' * 10
        user1 = self.create_user('user1@test.com')
        user2 = self.create_user('user2@test.com')
        digitalwok_user1 = self.create_digitalwork(user1)
        thumbnail_user1 = self.create_thumbnail(user1)
        piece_user1, _ = self.create_piece(
            user1,
            digitalwok_user1,
            thumbnail_user1,
            num_editions=2,
        )

        # create loan
        self.create_loan_piece(user1, user2.email, piece_user1.pk,
                               startdate=datetime.utcnow().date(),
                               enddate=datetime.utcnow().date() + timedelta(days=1),
                               password=password)
        # retrieve loan
        # TODO why?
        LoanPiece.objects.get(prev_owner=user1)
        loan_history = piece_user1.loan_history

        self.assertEqual(len(loan_history[0]), 2)


class LoanEditionTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                      APIUtilPiece, APIUtilLoanEdition, APIUtilEditionNotification):
    fixtures = ['licenses.json']

    def setUp(self):
        from ...models import Loan
        super(LoanEditionTest, self).setUp()
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
        Loan.objects.all().delete()

    def test_web_user_list_loans(self):
        from ...api import LoanEndpoint
        from ...models import Loan
        from ...serializers import LoanSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        loan = Loan.create(edition_alice, loanee=bob, owner=alice)
        loan.save()

        url = reverse('api:ownership:loan-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = LoanEndpoint.as_view({'get': 'list'})
        response = view(request)

        qs = Loan.objects.filter(Q(prev_owner=alice) | Q(new_owner=bob))
        serializer = LoanSerializer(qs, many=True, context={'request': request})
        response_db = json.loads(json.dumps({'success': True,
                                             'count': len(qs),
                                             'unfiltered_count': len(qs),
                                             'next': None,
                                             'previous': None,
                                             'loans': serializer.data}))
        self.assertEqual(ordered_dict(response.data), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        for loan in response.data['loans']:
            self.assertIn('edition', loan)
            self.assertNotIn('piece', loan)

    def test_web_user_retrieve_loan(self):
        from ...api import LoanEndpoint
        from ...models import Loan
        from ...serializers import LoanSerializer
        from util.util import ordered_dict
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        loan = Loan.create(edition_alice, loanee=bob, owner=alice)
        loan.save()

        factory = APIRequestFactory()
        url = reverse('api:ownership:loan-detail', kwargs={'pk': loan.pk} )
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = LoanEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=loan.pk)

        serializer = LoanSerializer(loan, context={'request': request})
        response_db = json.loads(json.dumps(serializer.data))

        self.assertEqual(ordered_dict(response.data['loan']), ordered_dict(response_db))
        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertIn('edition', response.data['loan'])
        self.assertNotIn('piece', response.data['loan'])

    def test_create_loan_edition(self):
        from ...api import LoanEndpoint
        from ...models import Loan
        from dynamicfixtures import _djroot_user, _alice, _bob, _registered_edition_alice

        password = 'secret-alice'
        _djroot_user()
        alice = _alice()
        bob = _bob()
        edition_alice = _registered_edition_alice()
        data = {
            'loanee': bob.email,
            'bitcoin_id': edition_alice,
            'startdate': datetime.utcnow().date(),
            'enddate': datetime.utcnow().date() + timedelta(days=1),
            'password': password,
            'terms': True
        }
        view = LoanEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        url = reverse('api:ownership:loan-list')
        request = factory.post(url, data)
        force_authenticate(request, user=alice)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check that the loan exists
        loans = Loan.objects.filter(edition=edition_alice)
        self.assertEqual(len(loans), 1)
        loan = loans[0]

        # check owners
        self.assertEqual(loan.prev_owner, alice)
        self.assertEqual(loan.new_owner, bob)

        # check the status is None (meaning unconfirmed)
        self.assertIsNone(loan.status)

        self.assertIn('loan', response.data)
        self.assertIn('edition', response.data['loan'])

    def testLoanRequestStatus(self):
        edition = self.editions_user1[0]

        # create loan
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id,
                                 startdate=datetime.utcnow().date(),
                                 enddate=datetime.utcnow().date() + timedelta(days=1),
                                 password=self.password)

        # retrieve edition notification
        response = self.retrieve_edition_notification(self.user2, edition.bitcoin_id)
        self.assertEqual(response.data['notification']['notification'],
                         [{'action': 'loan', 'action_str': 'Pending loan request', 'by': self.user1.username}])
