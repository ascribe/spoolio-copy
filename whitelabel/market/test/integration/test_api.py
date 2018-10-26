from __future__ import absolute_import

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework.test import force_authenticate, APIRequestFactory
from rest_framework import status

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from ownership.test.util import APIUtilConsign
from piece.test.util import APIUtilPiece
from users.test.util import APIUtilUsers

from whitelabel.market.api import MarketEndpoint, MarketUserEndpoint, MarketPieceEndpoint, MarketEditionEndpoint
from whitelabel.models import WhitelabelSettings
from whitelabel.test.util import APIUtilWhitelabel
from s3.test.mocks import MockAwsTestCase


class MarketEndpointTest(MockAwsTestCase,
                         APIUtilUsers,
                         APIUtilDigitalWork,
                         APIUtilThumbnail,
                         APIUtilPiece,
                         APIUtilWhitelabel):

    def setUp(self):
        super(MarketEndpointTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user@test.com')

        self.market = self.create_whitelabel_market(self.user1, amount=10)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.factory = APIRequestFactory()

    def test_list_web(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        # signup & activate user3
        view = MarketEndpoint.as_view({'get': 'list'})
        url = '/api/whitelabel/markets/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, pk=self.user1.pk)

        self.assertIs(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], len(WhitelabelSettings.objects.all()))
        self.assertEqual(response.data['count'], 10)


class MarketUserEndpointTest(TestCase,
                             APIUtilUsers,
                             APIUtilDigitalWork,
                             APIUtilThumbnail,
                             APIUtilPiece,
                             APIUtilWhitelabel):

    def setUp(self):
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

        self.user1 = self.create_user('user@test.com')
        self.market = self.create_whitelabel_market(self.user_admin, amount=1)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.factory = APIRequestFactory()

    def test_list_web(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        # signup & activate user3
        view = MarketUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/users/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(len(response.data['users']), 1)
        self.assertEqual(response.data['users'][0]['email'], self.user1.email)

    def test_acl_web_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = MarketUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/users/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, domain_pk=self.market.subdomain)
        web_user = response.data['users'][0]
        user_acl = web_user['acl']

        self.assertTrue(user_acl['acl_create_piece'])
        self.assertTrue(user_acl['acl_wallet_submit'])
        self.assertTrue(user_acl['acl_consign'])

        self.assertFalse(user_acl['acl_transfer'])
        self.assertFalse(user_acl['acl_edit_public_contract'])
        self.assertFalse(user_acl['acl_update_public_contract'])
        self.assertFalse(user_acl['acl_view_settings_contract'])

    def test_acl_admin_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = MarketUserEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/users/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user_admin)

        response = view(request, domain_pk=self.market.subdomain)
        admin_user = response.data['users'][0]
        user_acl = admin_user['acl']
        self.assertTrue(user_acl['acl_transfer'])
        self.assertTrue(user_acl['acl_edit_public_contract'])
        self.assertFalse(user_acl['acl_update_public_contract'])
        self.assertTrue(user_acl['acl_view_settings_contract'])

        self.assertFalse(user_acl['acl_consign'])
        self.assertFalse(user_acl['acl_create_piece'])
        self.assertFalse(user_acl['acl_wallet_submit'])


class MarketPieceEndpointTest(MockAwsTestCase,
                              APIUtilUsers,
                              APIUtilDigitalWork,
                              APIUtilThumbnail,
                              APIUtilPiece,
                              APIUtilWhitelabel):

    fixtures = ['licenses.json']

    def setUp(self):
        super(MarketPieceEndpointTest, self).setUp()
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

        self.user1 = self.create_user('user@test.com')
        self.market = self.create_whitelabel_market(self.user_admin, amount=1)
        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
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
        view = MarketPieceEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/pieces/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(response.data['count'], 1)

    def test_list_web_admin(self):
        """
        Test that an admin user can see no pieces if there are non consigned to him
        He should not have access to the other pieces in the db.
        """
        view = MarketPieceEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/pieces/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user_admin)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(response.data['count'], 0)


class MarketEditionEndpointTest(MockAwsTestCase,
                                APIUtilUsers,
                                APIUtilDigitalWork,
                                APIUtilThumbnail,
                                APIUtilPiece,
                                APIUtilWhitelabel,
                                APIUtilConsign):

    fixtures = ['licenses.json']

    def setUp(self):
        super(MarketEditionEndpointTest, self).setUp()
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)

        self.user1 = self.create_user('user@test.com')
        self.market = self.create_whitelabel_market(self.user_admin, amount=1)
        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwork_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)
        self.factory = APIRequestFactory()

    def test_list_web_user(self):
        """
        Test that a web user can only see his own editions.
        He should not have access to the other pieces in the db.
        """
        view = MarketEditionEndpoint.as_view({'get': 'list'})

        url = '/api/whitelabel/markets/{}/editions/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(response.data['count'], len(self.editions_user1))

    def test_list_web_admin(self):
        """
        Test that an admin user can see no editions if there are non consigned to him
        He should not have access to the other pieces in the db.
        """
        view = MarketEditionEndpoint.as_view({'get': 'list'})
        url = '/api/whitelabel/markets/{}/editions/'.format(self.market.subdomain)
        request = self.factory.get(url)

        force_authenticate(request, user=self.market.user)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(response.data['count'], 0)

    def test_acl_edition_user(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = MarketEditionEndpoint.as_view({'get': 'retrieve'})

        edition_id = self.editions_user1[0].id
        url = '/api/whitelabel/markets/{}/editions/{}'.format(self.market.subdomain, edition_id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, pk=str(edition_id), domain_pk=self.market.subdomain)
        edition_acl = response.data['edition']['acl']

        self.assertTrue(edition_acl['acl_consign'])
        self.assertTrue(edition_acl['acl_wallet_submit'])
        self.assertTrue(edition_acl['acl_view_editions'])
        self.assertTrue(edition_acl['acl_download'])
        self.assertTrue(edition_acl['acl_share'])
        self.assertTrue(edition_acl['acl_view'])

        self.assertFalse(edition_acl['acl_unconsign'])
        self.assertFalse(edition_acl['acl_request_unconsign'])
        self.assertFalse(edition_acl['acl_transfer'])
        self.assertFalse(edition_acl['acl_withdraw_transfer'])
        self.assertFalse(edition_acl['acl_withdraw_consign'])
        self.assertFalse(edition_acl['acl_loan'])
        self.assertFalse(edition_acl['acl_delete'])
        self.assertFalse(edition_acl['acl_loan_request'])
        self.assertFalse(edition_acl['acl_wallet_submitted'])
        self.assertFalse(edition_acl['acl_wallet_accepted'])

    def test_acl_edition_admin(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """
        view = MarketEditionEndpoint.as_view({'get': 'retrieve'})

        piece_admin, editions_admin = self.create_piece(self.market.user,
                                                        self.digitalwork_user1,
                                                        self.thumbnail_user1,
                                                        num_editions=1)

        url = '/api/whitelabel/markets/{}/editions/{}'.format(self.market.subdomain, 1)
        request = self.factory.get(url)

        force_authenticate(request, user=self.market.user)

        response = view(request, pk=editions_admin[0].bitcoin_id, domain_pk=self.market.subdomain)

        edition_acl = response.data['edition']['acl']
        self.assertTrue(edition_acl['acl_view_editions'])
        self.assertTrue(edition_acl['acl_download'])
        self.assertTrue(edition_acl['acl_share'])
        self.assertTrue(edition_acl['acl_view'])
        self.assertTrue(edition_acl['acl_transfer'])

        self.assertFalse(edition_acl['acl_unconsign'])
        self.assertFalse(edition_acl['acl_consign'])
        self.assertFalse(edition_acl['acl_request_unconsign'])
        self.assertFalse(edition_acl['acl_withdraw_transfer'])
        self.assertFalse(edition_acl['acl_loan'])
        self.assertFalse(edition_acl['acl_delete'])
        self.assertFalse(edition_acl['acl_loan_request'])
        self.assertFalse(edition_acl['acl_wallet_submit'])
        self.assertFalse(edition_acl['acl_wallet_submitted'])
        self.assertFalse(edition_acl['acl_wallet_accepted'])

    def test_acl_edition_submit(self):
        """
        Test that a web user can only see his own pieces.
        He should not have access to the other pieces in the db.
        """

        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.market.user.email, edition.bitcoin_id, self.password)

        view = MarketEditionEndpoint.as_view({'get': 'list'})
        url = '/api/whitelabel/markets/{}/editions'.format(self.market.subdomain, 1)
        request = self.factory.get(url)

        force_authenticate(request, user=self.market.user)

        response = view(request, domain_pk=self.market.subdomain)

        self.assertEqual(response.data['count'], 1)

        edition_acl = response.data['editions'][0]['acl']

        self.assertTrue(edition_acl['acl_view_editions'])
        self.assertTrue(edition_acl['acl_download'])
        self.assertTrue(edition_acl['acl_share'])
        self.assertTrue(edition_acl['acl_view'])

        self.assertFalse(edition_acl['acl_consign'])
        self.assertFalse(edition_acl['acl_wallet_submit'])
        self.assertFalse(edition_acl['acl_unconsign'])
        self.assertFalse(edition_acl['acl_request_unconsign'])
        self.assertFalse(edition_acl['acl_transfer'])
        self.assertFalse(edition_acl['acl_withdraw_transfer'])
        self.assertFalse(edition_acl['acl_withdraw_consign'])
        self.assertFalse(edition_acl['acl_loan'])
        self.assertFalse(edition_acl['acl_delete'])
        self.assertFalse(edition_acl['acl_loan_request'])
        self.assertFalse(edition_acl['acl_wallet_submitted'])
        self.assertFalse(edition_acl['acl_wallet_accepted'])

        view = MarketEditionEndpoint.as_view({'get': 'retrieve'})
        url = '/api/whitelabel/markets/{}/editions'.format(self.market.subdomain, 1)
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)
        response = view(request, pk=edition.bitcoin_id, domain_pk=self.market.subdomain)

        edition = response.data['edition']
        edition_acl = edition['acl']

        self.assertTrue(edition_acl['acl_wallet_submitted'])
        self.assertTrue(edition_acl['acl_view_editions'])
        self.assertTrue(edition_acl['acl_download'])
        self.assertTrue(edition_acl['acl_share'])
        self.assertTrue(edition_acl['acl_view'])
        self.assertTrue(edition_acl['acl_withdraw_consign'])

        self.assertFalse(edition_acl['acl_consign'])
        self.assertFalse(edition_acl['acl_wallet_submit'])
        self.assertFalse(edition_acl['acl_unconsign'])
        self.assertFalse(edition_acl['acl_request_unconsign'])
        self.assertFalse(edition_acl['acl_transfer'])
        self.assertFalse(edition_acl['acl_withdraw_transfer'])
        self.assertFalse(edition_acl['acl_loan'])
        self.assertFalse(edition_acl['acl_delete'])
        self.assertFalse(edition_acl['acl_loan_request'])
        self.assertFalse(edition_acl['acl_wallet_accepted'])


# TODO This class has been written for the purpose of troubleshooting issue #70
# https://github.com/ascribe/spoolio/issues/70
# It is written separately because of its different appraoch, such as not
# relying on a setUp method that may perform operations that are not required
# by some test methods. This approach shoudl help to speed up tests executions.
class MarketApiTests(MockAwsTestCase):

    def test_acl_edit_of_a_retrieved_transferred_edition(self):
        from dynamicfixtures import (
            _djroot_user,
            _alice,
            _bob,
            _bob_bitcoin_wallet,
            _registered_edition_pair_alice,
            _whitelabel_merlin,
        )
        from bitcoin import tasks
        from bitcoin.models import BitcoinTransaction, BitcoinWallet
        from ownership.models import OwnershipRegistration, OwnershipTransfer
        from util import util
        _djroot_user()
        alice, bob = _alice(), _bob()
        _bob_bitcoin_wallet()
        edition_one, edition_two = _registered_edition_pair_alice()

        # TODO Extract, and/or simplify to the essentials.
        #
        # What are the essentials?
        # - Having two editions.
        # - The two editions belong to the same piece.
        # - The piece has been registered by alice.
        # - One edition has been transferred to bob.
        # - The transferred edition should have its acl_edit set accordingly.
        #
        # So, it may very well be possible to avoid going through all the
        # transfer related operations. Waht matters is that the transferred
        # edition has its fields set like it would have if it would have been
        # transferred. Related objects, which are created and/or modified
        # during a transfer may alos need to be created.
        OwnershipRegistration.objects.create(
            edition=edition_one,
            new_owner=edition_one.owner,
            piece=edition_one.parent,
            type=OwnershipRegistration.__name__,
        )
        transfer = OwnershipTransfer(
            edition=edition_one,
            prev_owner=edition_one.owner,
            new_owner=bob,
            prev_btc_address=None,
            piece=edition_one.parent,
            type=OwnershipTransfer.__name__,
        )
        transfer.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(
            transfer,
            'alice-secret',
        )
        transfer.save()
        transfer_tx = BitcoinTransaction.transfer(transfer)
        refill = BitcoinTransaction.refill(transfer)
        refill.dependent_tx = transfer_tx
        refill.save()
        tasks.refill(refill.id, util.mainAdminPassword())
        edition_one.owner = bob
        edition_one.save()
        # END of transfer

        whitelabel = _whitelabel_merlin()
        subdomain = whitelabel.subdomain
        view = MarketEditionEndpoint.as_view({'get': 'retrieve'})

        url = reverse(
            'api:whitelabel:market:edition-detail',
            kwargs={'domain_pk': subdomain, 'pk': edition_two.bitcoin_id},
        )
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)

        response = view(
            request, pk=edition_two.bitcoin_id, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['edition']['acl']['acl_edit'])
        self.assertTrue(response.data['edition']['acl']['acl_wallet_submit'])
