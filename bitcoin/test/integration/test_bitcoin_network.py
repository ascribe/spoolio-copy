from transactions import Transactions

from unittest import SkipTest
from mock import patch
from time import sleep

from datetime import datetime, timedelta

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection
from django.apps import apps

from rest_framework.test import APIRequestFactory, force_authenticate

from piece.test.util import APIUtilPiece
from bitcoin.models import BitcoinTransaction, BitcoinWallet, TX_CONFIRMED, TX_PENDING
from bitcoin.api import BitcoinNewBlockEndpoint
from bitcoin.tasks import check_status, create_refill_chunks, refill_main_wallet, initialize, import_address
from blobs.test.util import APIUtilThumbnail, APIUtilDigitalWork
from ownership.models import OwnershipPiece, Ownership, OwnershipEditions, OwnershipRegistration, OwnershipTransfer
from ownership.models import Consignment, UnConsignment, Loan, ConsignedRegistration, LoanPiece, OwnershipMigration
from ownership.test.util import APIUtilTransfer, APIUtilConsign, APIUtilUnconsign, APIUtilLoanPiece, APIUtilLoanEdition
from users.test.util import APIUtilUsers


# Use Cases:
# 1. Register Piece withouth number of editions
# 2. Register number of editions
# 3. Register Piece with number of editions
# 4. Consigned registration
# 5. Transfer to a registered user
# 6. Transfer to a non registered user
# 7. Transfer after changing password
# 8. Create a consignment -> confirm a consignment
# 9. Create a consignment -> change password -> confirm consignment
# 10. Change password -> create consignment -> confirm consignment
# 11. Create a consignment -> confirm a consignment -> Change password -> do another action
# 12. Unconsign
# 13. Change password -> unconsign
# 14. Loan edition -> confirm loan
# 15. Change password -> loan edition -> confirm loan
# 16. loan edition -> change password -> confirm loan
# 17. Loan piece -> confirm loan
# 18. Change password -> loan piece -> confirm loan
# 19. loan piece -> change password -> confirm loan


def blocktrail_call_webhook(txid, conf):
    from applications.tests.util import APIUtilApplications
    # create token for the webhook call
    blocktrail_user = APIUtilUsers.create_user('blocktrail@test.com')
    blocktrail_application = APIUtilApplications.create_application(blocktrail_user, 'blocktrail')
    blocktrail_token = APIUtilApplications.create_token(blocktrail_user,
                                                        blocktrail_application)
    factory = APIRequestFactory()

    data = {
        'event_type': 'transaction',
        'data': {
            'hash': txid,
            'confirmations': conf
        }
    }

    view = BitcoinNewBlockEndpoint.as_view()
    request = factory.post(reverse('api:bitcoin:confirmations'),
                           data=data,
                           HTTP_AUTHORIZATION='Bearer {}'.format(blocktrail_token),
                           format='json')
    force_authenticate(request, user=blocktrail_user)

    response = view(request)
    assert response.status_code == 200


def blocktrail_subscribe_mock(self, txid):
    """
    Blocktrail does not have access to our private regtest network so we have to mock the blocktrail network

    1. Query to regtest network using the bitcoin daemon for the status of the transaction
    2. If it is confirmed call the webhook
    """
    print 'Subscribing to events on', txid

    retry_count = 0
    conf = 0
    while retry_count < 5:
        conf = self.transactions.get(txid).get('confirmations', 0)

        if conf > 0:
            blocktrail_call_webhook(txid, conf)
            return
        else:
            retry_count += 1
            sleep(5)

    raise Exception('Transaction not confirmed')


def transactions_get_unspents_chunks(*args, **kwargs):
    # Test the creation of refill chunks
    return {'unspents': []}


def transactions_get_unspents_federation(*args, **kwargs):
    # To test the refill of the federation wallet there needs to be chunks
    return {'unspents': [{'amount': settings.BTC_CHUNK,
                          'confirmations': 1,
                          'vout': 1}] * 5}


class BitcoinNetworkTestCase(TestCase, APIUtilThumbnail, APIUtilDigitalWork, APIUtilPiece, APIUtilUsers,
                             APIUtilTransfer, APIUtilConsign, APIUtilUnconsign, APIUtilLoanEdition, APIUtilLoanPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        if settings.DEPLOYMENT != 'regtest' and not settings.BTC_ENABLED:
            raise SkipTest('Test class requires DEPLOYMENT=regtest and BTC_ENABLED=True')

        self.password1 = '0' * 10
        self.password2 = '1' * 10
        self.new_password = '2' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com', password=self.password1)
        self.user2 = self.create_user('user2@test.com', password=self.password2)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        Ownership.objects.all().delete()
        BitcoinTransaction.objects.all().delete()
        self.initialize_federation_wallet()

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_register_piece_no_editions(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)

        ownership_piece = OwnershipPiece.objects.get(piece=piece)
        self.assertIsNone(ownership_piece.ciphertext_wif)

        btc_piece = BitcoinTransaction.objects.get(ownership__piece=piece)
        self.assertEqual(btc_piece.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 1)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_register_piece_with_editions(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)

        ownership_piece = Ownership.objects.filter(piece=piece)
        self.assertEqual(len(ownership_piece), 2)
        for o in ownership_piece:
            self.assertIsNone(o.ciphertext_wif)

        btc_piece = BitcoinTransaction.objects.filter(ownership__piece=piece)
        self.assertEqual(len(btc_piece), 2)
        for btc in btc_piece:
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 2)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_register_number_editions(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.create_editions(self.user1, piece, 10)

        ownership_editions = OwnershipEditions.objects.get(piece=piece)
        self.assertIsNone(ownership_editions.ciphertext_wif)

        btc_editions = BitcoinTransaction.objects.get(ownership__type='OwnershipEditions')
        self.assertEqual(btc_editions.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 2)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_consigned_registration_without_editions(self, mock_unsubscribe):
        piece, editions = self.create_consigned_registration(self.user1, self.digitalwork_user1,
                                                             self.thumbnail_user1, num_editions=0)
        ownership_consigned = ConsignedRegistration.objects.get(piece=piece)
        self.assertEqual(Ownership.objects.count(), 1)
        self.assertIsNone(ownership_consigned.ciphertext_wif)
        btc_piece = BitcoinTransaction.objects.get(ownership__piece=piece)
        self.assertEqual(btc_piece.status, TX_CONFIRMED)
        self.assertEqual(mock_unsubscribe.call_count, 1)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_consigned_registration_with_editions(self, mock_unsubscribe):
        piece, editions = self.create_consigned_registration(self.user1, self.digitalwork_user1,
                                                             self.thumbnail_user1, num_editions=10)
        self.assertTrue(ConsignedRegistration.objects.filter(piece=piece).exists())
        self.assertTrue(OwnershipEditions.objects.filter(piece=piece).exists())
        btc_piece = BitcoinTransaction.objects.filter(ownership__piece=piece)
        self.assertEqual(len(btc_piece), 2)
        for btc in btc_piece:
            self.assertEqual(btc.status, TX_CONFIRMED)
        self.assertEqual(mock_unsubscribe.call_count, 2)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_transfer_edition(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.password1)

        self.assertEqual(Ownership.objects.count(), 4)
        # bitcoin has +1 that ownership because of the fuel transaction that we do not store on the ownership table
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 4)
        self.assertTrue(OwnershipRegistration.objects.filter(edition=edition).exists())
        self.assertTrue(OwnershipTransfer.objects.filter(edition=edition).exists())

        for btc in BitcoinTransaction.objects.filter(ownership__edition=edition):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_consign_edition(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password1)

        # Before confirm
        self.assertEqual(Ownership.objects.count(), 4)
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 3)
        self.assertTrue(OwnershipRegistration.objects.filter(edition=edition).exists())
        self.assertTrue(Consignment.objects.filter(edition=edition).exists())

        btc = BitcoinTransaction.objects.get(ownership__edition=edition)
        self.assertEqual(btc.status, TX_CONFIRMED)

        # after consign confirm
        self.confirm_consign(self.user2, edition.bitcoin_id)

        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 4)
        for btc in BitcoinTransaction.objects.filter(ownership__piece=piece):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_unconsign_edition(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password1)
        self.confirm_consign(self.user2, edition.bitcoin_id)
        self.create_unconsign(self.user2, edition.bitcoin_id, self.password2)

        self.assertTrue(UnConsignment.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 3)

        for btc in BitcoinTransaction.objects.filter(ownership__edition=edition):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 7)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_loan_editions(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                 enddate=enddate, password=self.password1)

        # Before confirm
        self.assertEqual(Ownership.objects.count(), 4)
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 3)
        self.assertTrue(OwnershipRegistration.objects.filter(edition=edition).exists())
        self.assertTrue(Loan.objects.filter(edition=edition).exists())

        btc = BitcoinTransaction.objects.get(ownership__edition=edition)
        self.assertEqual(btc.status, TX_CONFIRMED)

        # after loan confirm
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)

        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 4)
        for btc in BitcoinTransaction.objects.filter(ownership__piece=piece):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_loan_piece(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                               enddate=enddate, password=self.password1)

        # Before confirm
        self.assertEqual(Ownership.objects.count(), 2)
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 1)
        self.assertFalse(OwnershipRegistration.objects.exists())
        self.assertTrue(LoanPiece.objects.filter(piece=piece).exists())

        btc = BitcoinTransaction.objects.get(ownership__piece=piece)
        self.assertEqual(btc.status, TX_CONFIRMED)

        # after loan confirm
        self.confirm_loan_piece(self.user2, piece.id)

        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 2)
        for btc in BitcoinTransaction.objects.filter(ownership__piece=piece):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 3)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_loan_piece_request_confirm_flow(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.request_loan_piece(self.user2, piece.id, startdate=startdate,
                                enddate=enddate)

        # Before confirm
        self.assertEqual(Ownership.objects.count(), 2)
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 1)
        self.assertFalse(OwnershipRegistration.objects.exists())
        self.assertTrue(LoanPiece.objects.filter(piece=piece).exists())

        btc = BitcoinTransaction.objects.get(ownership__piece=piece)
        self.assertEqual(btc.status, TX_CONFIRMED)

        # after loan confirm
        self.request_confirm_loan_piece(self.user1, piece.id, self.password1)

        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 2)
        for btc in BitcoinTransaction.objects.filter(ownership__piece=piece):
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 3)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_transfer(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)

        self.assertTrue(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 6)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_consign_before_password_change(self, mock_unsubscribe):
        # If the consignment is created before the password change there will be no migration because the correct
        # wif was stored

        # create consign
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password1)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        self.assertFalse(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 2)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_consign_after_password_change(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # create consign
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)
        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        self.assertTrue(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 6)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_unconsign(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password1)
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # reset password user2
        self.request_reset_password(self.user2)
        self.reset_password(self.user2, self.new_password)

        # create unconsign
        self.create_unconsign(self.user2, edition.bitcoin_id, self.new_password)

        self.assertTrue(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 4)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 8)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_edition_before_password_change(self, mock_unsubscribe):
        # If the loan is created before the password change there will be no migration because the correct
        # wif was stored

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                 enddate=enddate, password=self.password1)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm loan
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)

        self.assertFalse(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 2)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_edition_after_password_change(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # create loan
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                 enddate=enddate, password=self.new_password)
        # confirm loan
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)

        self.assertTrue(OwnershipMigration.objects.filter(edition=edition).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__edition=edition).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 6)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_piece_before_password_change(self, mock_unsubscribe):
        # If the loan is created before the password change there will be no migration because the correct
        # wif was stored

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                               enddate=enddate, password=self.password1)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm loan
        self.confirm_loan_piece(self.user2, piece.id)

        self.assertFalse(OwnershipMigration.objects.filter(piece=piece, edition=None).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 2)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 3)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_piece_after_password_change(self, mock_unsubscribe):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # create loan
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                               enddate=enddate, password=self.new_password)
        # confirm loan
        self.confirm_loan_piece(self.user2, piece.id)

        self.assertTrue(OwnershipMigration.objects.filter(piece=piece).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 4)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_piece_request_confirm_flow_before_password_change(self, mock_unsubscribe):
        # This case is different from the loan_piece because the loan ownership object is created
        # when the loanee requests a loan a so we do not store the password that would allow us to
        # perform the migration

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.request_loan_piece(self.user2, piece.id, startdate=startdate,
                                enddate=enddate)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm loan
        self.request_confirm_loan_piece(self.user1, piece.id, self.new_password)

        self.assertTrue(OwnershipMigration.objects.filter(piece=piece, edition=None).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 4)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_migration_loan_piece_request_confirm_flow_after_password_change(self, mock_unsubscribe):
        # This case is different from the loan_piece because the loan ownership object is created
        # when the loanee requests a loan a so we do not store the password that would allow us to
        # perform the migration

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        self.request_loan_piece(self.user2, piece.id, startdate=startdate,
                                enddate=enddate)

        # confirm loan
        self.request_confirm_loan_piece(self.user1, piece.id, self.new_password)

        self.assertTrue(OwnershipMigration.objects.filter(piece=piece, edition=None).exists())
        self.assertEqual(BitcoinTransaction.objects.filter(ownership__piece=piece).count(), 3)

        for o in Ownership.objects.all():
            self.assertIsNone(o.ciphertext_wif)

        for btc in BitcoinTransaction.objects.all():
            self.assertEqual(btc.status, TX_CONFIRMED)

        self.assertEqual(mock_unsubscribe.call_count, 4)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe')
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_create_refill_chunks(self, mock_unsubscribe, mock_subscribe):
        t = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET, username=settings.BTC_USERNAME,
                         password=settings.BTC_PASSWORD, host=settings.BTC_HOST, port=settings.BTC_PORT)
        unspents = t.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
        refill_chuncks_before = filter(lambda d: d['amount'] == settings.BTC_CHUNK, unspents)
        create_refill_chunks.delay()
        unspents = t.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
        refill_chuncks_after = filter(lambda d: d['amount'] == settings.BTC_CHUNK, unspents)
        self.assertEqual(len(refill_chuncks_after), len(refill_chuncks_before) + 5)

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe')
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_refill_main_wallet(self, mock_unsubscribe, mock_subscribe):
        t = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET, username=settings.BTC_USERNAME,
                         password=settings.BTC_PASSWORD, host=settings.BTC_HOST, port=settings.BTC_PORT)
        unspents = t.get(settings.BTC_MAIN_WALLET, min_confirmations=1).get('unspents', [])
        fees_before = filter(lambda d: d['amount'] == settings.BTC_FEE, unspents)
        tokens_before = filter(lambda d: d['amount'] == settings.BTC_TOKEN, unspents)
        refill_main_wallet.delay()
        unspents = t.get(settings.BTC_MAIN_WALLET, min_confirmations=1).get('unspents', [])
        fees_after = filter(lambda d: d['amount'] == settings.BTC_FEE, unspents)
        tokens_after = filter(lambda d: d['amount'] == settings.BTC_TOKEN, unspents)
        self.assertEqual(len(fees_after), len(fees_before) + 50)
        self.assertEqual(len(tokens_after), len(tokens_before) + 150)

    @patch('bitcoin.tasks.create_refill_chunks')
    @patch('bitcoin.tasks.send_low_funds_email')
    @patch('bitcoin.tasks.refill_main_wallet')
    @patch('transactions.Transactions.get', new=transactions_get_unspents_chunks)
    def test_check_status_refill_chunks(self, mock_refill_main_wallet, mock_send_low_funds_email, mock_refill_chuncks):
        check_status.delay()
        self.assertEqual(mock_refill_chuncks.delay.call_count, 1)

    @patch('bitcoin.tasks.create_refill_chunks')
    @patch('bitcoin.tasks.send_low_funds_email')
    @patch('bitcoin.tasks.refill_main_wallet')
    @patch('transactions.Transactions.get', new=transactions_get_unspents_federation)
    def test_check_status_refill_federation_wallet(self, mock_refill_main_wallet, mock_send_low_funds_email,
                                                   mock_refill_chuncks):
        check_status.delay()
        self.assertEqual(mock_refill_main_wallet.delay.call_count, 2)
        self.assertEqual(mock_send_low_funds_email.delay.call_count, 1)

    def test_import_address(self):
        t = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET, username=settings.BTC_USERNAME,
                         password=settings.BTC_PASSWORD, host=settings.BTC_HOST, port=settings.BTC_PORT)

        with self.settings(BTC_ENABLED=False):
            address = BitcoinWallet.walletForUser(self.user1).create_new_address()
            BitcoinWallet.import_address(address, self.user1).delay()
            address = address.split(':')[1]

        # with btc disabled the address should not be imported
        response = t._service.make_request('getaddressesbyaccount', [self.user1.email])
        self.assertIsNone(response['error'])
        self.assertFalse(address in response['result'])

        # lets import it
        import_address(address, self.user1.email)
        response = t._service.make_request('getaddressesbyaccount', [self.user1.email])
        self.assertIsNone(response['error'])
        self.assertTrue(address in response['result'])

        # lets create a new address with btc enabled
        address = BitcoinWallet.walletForUser(self.user1).create_new_address()
        BitcoinWallet.import_address(address, self.user1).delay()
        address = address.split(':')[1]
        response = t._service.make_request('getaddressesbyaccount', [self.user1.email])
        self.assertIsNone(response['error'])
        self.assertTrue(address in response['result'])

    # Initialize federation wallet here
    @staticmethod
    def initialize_federation_wallet():
        FederationWallet = apps.get_model(app_label='bitcoin', model_name='FederationWallet')
        print 'Resetting the FederationWallet'
        FederationWallet.objects.all().delete()

        # Reset the ids after deleting all the rows
        cursor = connection.cursor()
        cursor.execute("ALTER SEQUENCE bitcoin_federationwallet_id_seq RESTART WITH 1")

        print 'Populating federation wallet with unspents'
        transactions = Transactions(service='daemon', username=settings.BTC_USERNAME,
                                    password=settings.BTC_PASSWORD, host=settings.BTC_HOST,
                                    port=settings.BTC_PORT, testnet=settings.BTC_TESTNET)
        unspents = transactions.get(settings.BTC_MAIN_WALLET, min_confirmations=1).get('unspents', [])
        for unspent in unspents:
            if unspent['amount'] in [settings.BTC_TOKEN, settings.BTC_FEE]:
                # main wallet
                unspent.update({'type': 'main'})
                FederationWallet(**unspent).save()

        unspents = transactions.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
        for unspent in unspents:
            if unspent['amount'] == settings.BTC_CHUNK:
                # main wallet
                unspent.update({'type': 'refill'})
                FederationWallet(**unspent).save()

        print 'Finished initializing wallet'


class BitcoinNetworkInitializationTestCase(TestCase, APIUtilThumbnail, APIUtilDigitalWork, APIUtilPiece, APIUtilUsers,
                                           APIUtilTransfer, APIUtilConsign, APIUtilUnconsign,
                                           APIUtilLoanEdition, APIUtilLoanPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        if settings.DEPLOYMENT != 'regtest' and not settings.BTC_ENABLED:
            raise SkipTest('Test class requires DEPLOYMENT=regtest and BTC_ENABLED=True')

        self.password1 = '0' * 10
        self.password2 = '1' * 10
        self.new_password = '2' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com', password=self.password1)
        self.user2 = self.create_user('user2@test.com', password=self.password2)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.initialize_federation_wallet()

    @patch('bitcoin.tasks.SpoolAction.blocktrail_subscribe', new=blocktrail_subscribe_mock)
    @patch('bitcoin.tasks.SpoolAction.blocktrail_unsubscribe')
    def test_initialization(self, mock_unsubscribe):
        with self.settings(BTC_ENABLED=False):
            # Do a bunch of ownership operations
            piece, editions = self.create_piece(self.user1, self.digitalwork_user1,
                                                self.thumbnail_user1, num_editions=10)
            self.create_consigned_registration(self.user1, self.digitalwork_user1,
                                               self.thumbnail_user1, num_editions=10)
            editions = list(editions)
            edition = editions[0]
            self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.password1)
            edition = editions[1]
            self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password1)
            self.confirm_consign(self.user2, edition.bitcoin_id)
            self.create_unconsign(self.user2, edition.bitcoin_id, self.password2)
            startdate = datetime.utcnow().date()
            enddate = datetime.utcnow().date() + timedelta(days=1)
            edition = editions[2]
            self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                     enddate=enddate, password=self.password1)
            self.confirm_loan_edition(self.user2, edition.bitcoin_id)
            self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                                   enddate=enddate, password=self.password1)
            self.confirm_loan_piece(self.user2, piece.id)
            edition = editions[3]
            self.request_reset_password(self.user1)
            self.reset_password(self.user1, self.new_password)
            self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)
        # check the status of the transactions
        for o in Ownership.objects.all():
            self.assertIsNotNone(o.btc_tx)

        for t in BitcoinTransaction.objects.all():
            self.assertEqual(t.status, TX_PENDING)

        # initialize
        initialize.delay()

        for t in BitcoinTransaction.objects.all():
            self.assertEqual(t.status, TX_CONFIRMED)

    # Initialize federation wallet here
    @staticmethod
    def initialize_federation_wallet():
        FederationWallet = apps.get_model(app_label='bitcoin', model_name='FederationWallet')
        print 'Resetting the FederationWallet'
        FederationWallet.objects.all().delete()

        # Reset the ids after deleting all the rows
        cursor = connection.cursor()
        cursor.execute("ALTER SEQUENCE bitcoin_federationwallet_id_seq RESTART WITH 1")

        print 'Populating federation wallet with unspents'
        transactions = Transactions(service='daemon', username=settings.BTC_USERNAME,
                                    password=settings.BTC_PASSWORD, host=settings.BTC_HOST,
                                    port=settings.BTC_PORT, testnet=settings.BTC_TESTNET)
        unspents = transactions.get(settings.BTC_MAIN_WALLET, min_confirmations=1).get('unspents', [])
        for unspent in unspents:
            if unspent['amount'] in [settings.BTC_TOKEN, settings.BTC_FEE]:
                # main wallet
                unspent.update({'type': 'main'})
                FederationWallet(**unspent).save()

        unspents = transactions.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
        for unspent in unspents:
            if unspent['amount'] == settings.BTC_CHUNK:
                # main wallet
                unspent.update({'type': 'refill'})
                FederationWallet(**unspent).save()

        print 'Finished initializing wallet'
