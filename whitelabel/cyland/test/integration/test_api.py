from __future__ import absolute_import
from datetime import timedelta

from django.test import TestCase
from django.conf import settings
from django.utils.datetime_safe import datetime

from rest_framework.test import force_authenticate, APIRequestFactory

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from ownership.test.util import APIUtilContractAgreement, APIUtilLoanPiece
from piece.test.util import APIUtilPiece
from users.test.util import APIUtilUsers
from whitelabel.cyland.api import CylandUserEndpoint, CylandPieceEndpoint
from whitelabel.cyland.test.util import APIUtilWhitelabelCyland


class CylandUserEndpointTest(TestCase,
                             APIUtilUsers,
                             APIUtilDigitalWork,
                             APIUtilThumbnail,
                             APIUtilPiece,
                             APIUtilWhitelabelCyland,
                             APIUtilContractAgreement):
    def setUp(self):
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

        self.user1 = self.create_user('user@test.com')
        self.market = self.create_whitelabel_cyland(self.user_admin)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.factory = APIRequestFactory()

    def test_list_web(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        # signup & activate user3
        view = CylandUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/cyland/users/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request)

        self.assertEqual(len(response.data['users']), 1)
        self.assertEqual(response.data['users'][0]['email'], self.user1.email)

    def test_acl_web_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = CylandUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/cyland/users/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request)
        web_user = response.data['users'][0]
        user_acl = web_user['acl']
        self.assertTrue(user_acl['acl_create_piece'])
        self.assertTrue(user_acl['acl_wallet_submit'])
        self.assertTrue(user_acl['acl_loan'])

        self.assertFalse(user_acl['acl_edit_public_contract'])
        self.assertFalse(user_acl['acl_view_settings_contract'])

    def test_acl_admin_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = CylandUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/cyland/users/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user_admin)

        response = view(request)
        admin_user = response.data['users'][0]
        user_acl = admin_user['acl']
        self.assertFalse(user_acl['acl_create_piece'])
        self.assertFalse(user_acl['acl_wallet_submit'])
        self.assertFalse(user_acl['acl_loan'])

        self.assertTrue(user_acl['acl_edit_public_contract'])
        self.assertTrue(user_acl['acl_view_settings_contract'])


class CylandPieceEndpointTest(TestCase,
                              APIUtilUsers,
                              APIUtilDigitalWork,
                              APIUtilThumbnail,
                              APIUtilPiece,
                              APIUtilLoanPiece,
                              APIUtilWhitelabelCyland,
                              APIUtilContractAgreement):
    fixtures = ['licenses.json']

    def setUp(self):
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

        self.user1 = self.create_user('user@test.com')
        self.market = self.create_whitelabel_cyland(self.user_admin)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.factory = APIRequestFactory()

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwork_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)
        self.factory = APIRequestFactory()

    def test_list_web_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = CylandPieceEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/cyland/pieces/'
        request = self.factory.get(url)
        force_authenticate(request, user=self.user1)

        response = view(request)

        self.assertEqual(response.data['count'], 1)

    def test_list_web_admin(self):
        """
        Test that an admin user can see no editions if there are non consigned to him
        He should not have access to the other pieces in the db.
        """
        view = CylandPieceEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/cyland/pieces/'
        request = self.factory.get(url)
        force_authenticate(request, user=self.user_admin)

        response = view(request)

        self.assertEqual(response.data['count'], 0)

    def test_acl_piece_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = CylandPieceEndpoint.as_view({'get': 'retrieve'})

        piece_id = self.piece_user1.id
        url = '/api/whitelabel/cyland/pieces/{}'.format(self.market.subdomain, piece_id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, pk=str(piece_id))
        piece_acl = response.data['piece']['acl']

        self.assertTrue(piece_acl['acl_download'])
        self.assertTrue(piece_acl['acl_share'])
        self.assertTrue(piece_acl['acl_view'])
        self.assertTrue(piece_acl['acl_loan'])
        self.assertTrue(piece_acl['acl_wallet_submit'])

        self.assertFalse(piece_acl['acl_consign'])
        self.assertFalse(piece_acl['acl_unconsign'])
        self.assertFalse(piece_acl['acl_view_editions'])
        self.assertFalse(piece_acl['acl_request_unconsign'])
        self.assertFalse(piece_acl['acl_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_consign'])
        self.assertFalse(piece_acl['acl_delete'])
        self.assertFalse(piece_acl['acl_loan_request'])
        self.assertFalse(piece_acl['acl_wallet_submitted'])
        self.assertFalse(piece_acl['acl_wallet_accepted'])

    def test_acl_piece_admin(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = CylandPieceEndpoint.as_view({'get': 'retrieve'})

        piece_admin, editions_admin = self.create_piece(self.market.user,
                                                        self.digitalwork_user1,
                                                        self.thumbnail_user1,
                                                        num_editions=1)

        url = '/api/whitelabel/cyland/pieces/{}'.format(self.market.subdomain, piece_admin.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.market.user)

        response = view(request, pk=piece_admin.id)

        piece_acl = response.data['piece']['acl']

        self.assertTrue(piece_acl['acl_download'])
        self.assertTrue(piece_acl['acl_share'])
        self.assertTrue(piece_acl['acl_view'])

        self.assertFalse(piece_acl['acl_consign'])
        self.assertFalse(piece_acl['acl_unconsign'])
        self.assertFalse(piece_acl['acl_view_editions'])
        self.assertFalse(piece_acl['acl_request_unconsign'])
        self.assertFalse(piece_acl['acl_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_consign'])
        self.assertFalse(piece_acl['acl_delete'])
        self.assertFalse(piece_acl['acl_loan_request'])
        self.assertFalse(piece_acl['acl_loan'])
        self.assertFalse(piece_acl['acl_wallet_submit'])
        self.assertFalse(piece_acl['acl_wallet_submitted'])
        self.assertFalse(piece_acl['acl_wallet_accepted'])

    def test_acl_piece_user_submit(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        piece = self.piece_user1
        ca = self.create_contractagreement(self.user_admin, self.user1)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)

        self.create_loan_piece(self.user1, self.market.user.email, piece.id, startdate, enddate,
                               password=self.password, contract_agreement_id=ca.id)

        view = CylandPieceEndpoint.as_view({'get': 'retrieve'})

        url = '/api/whitelabel/cyland/pieces/{}'.format(piece.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.market.user)

        response = view(request, pk=str(piece.id))

        piece_acl = response.data['piece']['acl']

        self.assertTrue(piece_acl['acl_download'])
        self.assertTrue(piece_acl['acl_share'])
        self.assertTrue(piece_acl['acl_view'])
        self.assertTrue(piece_acl['acl_loan_request'])

        self.assertFalse(piece_acl['acl_view_editions'])
        self.assertFalse(piece_acl['acl_consign'])
        self.assertFalse(piece_acl['acl_unconsign'])
        self.assertFalse(piece_acl['acl_request_unconsign'])
        self.assertFalse(piece_acl['acl_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_consign'])
        self.assertFalse(piece_acl['acl_delete'])
        self.assertFalse(piece_acl['acl_loan'])
        self.assertFalse(piece_acl['acl_wallet_submit'])
        self.assertFalse(piece_acl['acl_wallet_submitted'])
        self.assertFalse(piece_acl['acl_wallet_accepted'])

        force_authenticate(request, user=self.user1)

        response = view(request, pk=str(piece.id))

        piece_acl = response.data['piece']['acl']

        self.assertTrue(piece_acl['acl_wallet_submitted'])
        self.assertTrue(piece_acl['acl_download'])
        self.assertTrue(piece_acl['acl_share'])
        self.assertTrue(piece_acl['acl_view'])
        self.assertTrue(piece_acl['acl_loan'])

        self.assertFalse(piece_acl['acl_consign'])
        self.assertFalse(piece_acl['acl_wallet_submit'])
        self.assertFalse(piece_acl['acl_view_editions'])
        self.assertFalse(piece_acl['acl_unconsign'])
        self.assertFalse(piece_acl['acl_withdraw_consign'])
        self.assertFalse(piece_acl['acl_request_unconsign'])
        self.assertFalse(piece_acl['acl_transfer'])
        self.assertFalse(piece_acl['acl_withdraw_transfer'])
        self.assertFalse(piece_acl['acl_delete'])
        self.assertFalse(piece_acl['acl_loan_request'])
        self.assertFalse(piece_acl['acl_wallet_accepted'])

        # TODO: accept loan
