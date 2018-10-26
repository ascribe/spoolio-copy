from pycoin.key.BIP32Node import BIP32Node

from datetime import datetime, timedelta

from django.conf import settings

from bitcoin.models import BitcoinTransaction, BitcoinWallet, TX_PENDING
from bitcoin.bitcoin_service import BitcoinService
from users.test.util import APIUtilUsers
from blobs.test.util import APIUtilThumbnail, APIUtilDigitalWork
from piece.test.util import APIUtilPiece
from ownership.test.util import APIUtilTransfer, APIUtilConsign, APIUtilUnconsign, APIUtilLoanEdition, APIUtilLoanPiece
from ownership.models import Consignment, UnConsignment, Loan, LoanPiece, OwnershipMigration, OwnershipTransfer
from s3.test.mocks import MockAwsTestCase


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


class BitcoinTransactionTestCase(MockAwsTestCase,
                                 APIUtilUsers,
                                 APIUtilDigitalWork,
                                 APIUtilThumbnail,
                                 APIUtilPiece,
                                 APIUtilTransfer,
                                 APIUtilConsign,
                                 APIUtilUnconsign,
                                 APIUtilLoanEdition,
                                 APIUtilLoanPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        super(BitcoinTransactionTestCase, self).setUp()
        self.password = '0' * 10
        self.password2 = '1' * 10
        self.new_password = '2' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com', password=self.password)
        self.user2 = self.create_user('user2@test.com', password=self.password2)

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        # delete ownership
        BitcoinTransaction.objects.all().delete()

    def test_register_piece_no_editions(self):
        # create piece
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)

        # check piece address
        self.assertTrue(self._check_address(piece.bitcoin_path, self.user1, self.password))

        # retrieve transaction
        btc_tx = BitcoinTransaction.objects.get(ownership__piece=piece)

        self.assertEqual(btc_tx.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx.outputs[0], (BitcoinService.minDustSize, piece.hash_as_address_no_metada()))
        self.assertEqual(btc_tx.outputs[1], (BitcoinService.minDustSize, piece.hash_as_address()))
        self.assertEqual(btc_tx.outputs[2], (BitcoinService.minDustSize, piece.bitcoin_id))

        self.assertEqual(btc_tx.spoolverb, 'ASCRIBESPOOL01PIECE')
        self.assertEqual(btc_tx.status, TX_PENDING)

    def test_register_piece_with_editions(self):
        # create piece
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)

        # check edition address
        for edition in editions:
            self.assertTrue(self._check_address(edition.bitcoin_path, self.user1, self.password))

        # retrieve transactions
        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx = BitcoinTransaction.objects.get(ownership__type='OwnershipEditions')

        # piece + editions
        self.assertEqual(len(btc_txs), 2)

        self.assertEqual(btc_tx.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                          (BitcoinService.minDustSize, piece.hash_as_address()),
                                          (BitcoinService.minDustSize, piece.bitcoin_id)])

        self.assertEqual(btc_tx.spoolverb, 'ASCRIBESPOOL01EDITIONS10')
        self.assertEqual(btc_tx.status, TX_PENDING)

    def test_register_number_editions(self):
        # create piece
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.assertFalse(BitcoinTransaction.objects.filter(ownership__type='OwnershipEditions').exists())

        # create editions
        edition_task = self.create_editions(self.user1, piece, 10)
        btc_tx = BitcoinTransaction.objects.get(ownership__type='OwnershipEditions')

        self.assertEqual(btc_tx.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                          (BitcoinService.minDustSize, piece.hash_as_address()),
                                          (BitcoinService.minDustSize, piece.bitcoin_id)])

        self.assertEqual(btc_tx.spoolverb, 'ASCRIBESPOOL01EDITIONS10')
        self.assertEqual(btc_tx.status, TX_PENDING)

    def test_consigned_registration(self):
        piece, editions = self.create_consigned_registration(self.user1, self.digitalwork_user1,
                                                             self.thumbnail_user1, num_editions=10)
        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx = BitcoinTransaction.objects.get(ownership__type='ConsignedRegistration')

        # consigned registration + editions
        self.assertEqual(len(btc_txs), 2)

        for edition in editions:
            self.assertTrue(self._check_address(edition.bitcoin_path, self.user1, self.password))

        self.assertEqual(btc_tx.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                          (BitcoinService.minDustSize, piece.hash_as_address()),
                                          (BitcoinService.minDustSize, piece.bitcoin_id)])

        self.assertEqual(btc_tx.spoolverb, 'ASCRIBESPOOL01CONSIGNEDREGISTRATION')
        self.assertEqual(btc_tx.status, TX_PENDING)

    def test_transfer_edition(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_transfer = BitcoinTransaction.objects.get(ownership__type='OwnershipTransfer')
        btc_tx_register = BitcoinTransaction.objects.get(ownership__type='OwnershipRegistration')

        # piece + editions + register + transfer
        self.assertEqual(len(btc_txs), 4)

        # check registration
        self.assertEqual(btc_tx_register.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_register.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                   (BitcoinService.minDustSize, edition.hash_as_address()),
                                                   (BitcoinService.minDustSize, edition.bitcoin_id)])

        self.assertEqual(btc_tx_register.spoolverb, 'ASCRIBESPOOL01REGISTER{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_register.status, TX_PENDING)

        # check transfer
        self.assertTrue(self._check_address(edition.btc_owner_address, self.user2, self.password2))

        self.assertEqual(btc_tx_transfer.from_address, edition.bitcoin_path)
        self.assertEqual(btc_tx_transfer.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                   (BitcoinService.minDustSize, edition.btc_owner_address_noprefix)])

        self.assertEqual(btc_tx_transfer.spoolverb, 'ASCRIBESPOOL01TRANSFER{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_transfer.status, TX_PENDING)

    def test_consign_edition(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)

        # piece + edition + register
        self.assertEqual(len(btc_txs), 3)
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01PIECE').exists())
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01EDITIONS10').exists())
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01REGISTER{}'.
                                                          format(edition.edition_number)).exists())

        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        btc_tx_consign = BitcoinTransaction.objects.get(ownership__type='Consignment')

        # check consignment
        new_btc_path = Consignment.objects.get(edition=edition).new_btc_address
        _, new_address = new_btc_path.split(':')
        self.assertTrue(self._check_address(new_btc_path, self.user2, self.password2))

        self.assertEqual(btc_tx_consign.from_address, edition.bitcoin_path)
        self.assertEqual(btc_tx_consign.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, new_address)])

        self.assertEqual(btc_tx_consign.spoolverb, 'ASCRIBESPOOL01CONSIGN{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_consign.status, TX_PENDING)

    def test_unconsign_edition(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # create unconsign
        self.create_unconsign(self.user2, edition.bitcoin_id, self.password2)

        btc_tx_unconsign = BitcoinTransaction.objects.get(ownership__type='UnConsignment')
        ownership_unconsignment = UnConsignment.objects.get(edition=edition)
        prev_btc_path = ownership_unconsignment.prev_btc_address
        new_btc_path = ownership_unconsignment.new_btc_address
        _, new_address = new_btc_path.split(':')

        self.assertEqual(new_btc_path, edition.btc_owner_address)
        self.assertTrue(self._check_address(prev_btc_path, self.user2, self.password2))

        # check unconsignment
        self.assertEqual(btc_tx_unconsign.from_address, prev_btc_path)
        self.assertEqual(btc_tx_unconsign.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                    (BitcoinService.minDustSize, new_address)])

        self.assertEqual(btc_tx_unconsign.spoolverb, 'ASCRIBESPOOL01UNCONSIGN{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_unconsign.status, TX_PENDING)

    def test_loan_edition(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                 enddate=enddate, password=self.password)
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_loan = BitcoinTransaction.objects.get(ownership__type='Loan')
        ownership_loan = Loan.objects.get(edition=edition)

        # piece, editions, register, loan
        self.assertEqual(len(btc_txs), 4)
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01PIECE').exists())
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01EDITIONS10').exists())
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01REGISTER{}'.
                                                          format(edition.edition_number)).exists())

        # check loan
        new_btc_path = ownership_loan.new_btc_address
        _, new_address = new_btc_path.split(':')

        self.assertTrue(self._check_address(new_btc_path, self.user2, self.password2))

        self.assertEqual(btc_tx_loan.from_address, edition.bitcoin_path)
        self.assertEqual(btc_tx_loan.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                               (BitcoinService.minDustSize, new_address)])

        self.assertEqual(btc_tx_loan.spoolverb, 'ASCRIBESPOOL01LOAN{}/{}{}'.format(edition.edition_number,
                                                                                   startdate.strftime('%y%m%d'),
                                                                                   enddate.strftime('%y%m%d')))
        self.assertEqual(btc_tx_loan.status, TX_PENDING)

    def test_loan_piece(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                               enddate=enddate, password=self.password)
        self.confirm_loan_piece(self.user2, piece.id)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_loan = BitcoinTransaction.objects.get(ownership__type='LoanPiece')
        ownership_loan = LoanPiece.objects.get(piece=piece, edition=None)

        # piece, loan
        self.assertEqual(len(btc_txs), 2)
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01PIECE').exists())

        # check loan
        new_btc_path = ownership_loan.new_btc_address
        _, new_address = new_btc_path.split(':')

        self.assertTrue(self._check_address(new_btc_path, self.user2, self.password2))

        self.assertEqual(btc_tx_loan.from_address, piece.bitcoin_path)
        self.assertEqual(btc_tx_loan.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                               (BitcoinService.minDustSize, new_address)])

        self.assertEqual(btc_tx_loan.spoolverb, 'ASCRIBESPOOL01LOAN/{}{}'.format(startdate.strftime('%y%m%d'),
                                                                                 enddate.strftime('%y%m%d')))
        self.assertEqual(btc_tx_loan.status, TX_PENDING)

    def test_loan_piece_request_confirm_flow(self):
        # Ikono.tv test
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.request_loan_piece(self.user2, piece.id, startdate=startdate, enddate=enddate)
        self.request_confirm_loan_piece(self.user1, piece.id, self.password)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_loan = BitcoinTransaction.objects.get(ownership__type='LoanPiece')
        ownership_loan = LoanPiece.objects.get(piece=piece, edition=None)

        # piece, loan
        self.assertEqual(len(btc_txs), 2)
        self.assertTrue(BitcoinTransaction.objects.filter(spoolverb='ASCRIBESPOOL01PIECE').exists())

        # check loan
        new_btc_path = ownership_loan.new_btc_address
        _, new_address = new_btc_path.split(':')

        self.assertTrue(self._check_address(new_btc_path, self.user2, self.password2))

        self.assertEqual(btc_tx_loan.from_address, piece.bitcoin_path)
        self.assertEqual(btc_tx_loan.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                               (BitcoinService.minDustSize, new_address)])

        self.assertEqual(btc_tx_loan.spoolverb, 'ASCRIBESPOOL01LOAN/{}{}'.format(startdate.strftime('%y%m%d'),
                                                                                 enddate.strftime('%y%m%d')))
        self.assertEqual(btc_tx_loan.status, TX_PENDING)

    def test_migration_transfer(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_migrate = BitcoinTransaction.objects.get(ownership__type='OwnershipMigration')
        btc_tx_transfer = BitcoinTransaction.objects.get(ownership__type='OwnershipTransfer')
        ownership_migration = OwnershipMigration.objects.get(edition=edition)
        ownership_transfer = OwnershipTransfer.objects.get(edition=edition)

        # piece, editions, register, migration, transfer
        self.assertEqual(len(btc_txs), 5)

        # check migration
        new_btc_path_migration = ownership_migration.new_btc_address
        _, new_address_migration = new_btc_path_migration.split(':')

        self.assertTrue(self._check_address(new_btc_path_migration, self.user1, self.new_password))

        self.assertEqual(btc_tx_migrate.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_migrate.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, edition.bitcoin_id),
                                                  (BitcoinService.minDustSize, new_address_migration)])

        self.assertEqual(btc_tx_migrate.spoolverb, 'ASCRIBESPOOL01MIGRATE{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_migrate.status, TX_PENDING)

        # check transfer
        new_btc_path_transfer = ownership_transfer.new_btc_address
        _, new_address_transfer = new_btc_path_transfer.split(':')

        self.assertEqual(btc_tx_transfer.from_address, new_btc_path_migration)
        self.assertEqual(btc_tx_transfer.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                   (BitcoinService.minDustSize, new_address_transfer)])

        self.assertEqual(btc_tx_transfer.spoolverb, 'ASCRIBESPOOL01TRANSFER{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_transfer.status, TX_PENDING)

    def test_migration_consign_before_password_change(self):
        # If the consignment is created before the password change there will be no migration because the correct
        # wif was stored

        # create consign
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        self.assertFalse(OwnershipMigration.objects.filter(edition=edition).exists())

    def test_migration_consign_after_password_change(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # create consign
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)
        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_migrate = BitcoinTransaction.objects.get(ownership__type='OwnershipMigration')
        btc_tx_consign = BitcoinTransaction.objects.get(ownership__type='Consignment')
        ownership_migration = OwnershipMigration.objects.get(edition=edition)
        ownership_consign = Consignment.objects.get(edition=edition)

        # piece, editions, register, migration, consign
        self.assertEqual(len(btc_txs), 5)

        # check migration
        new_btc_path_migration = ownership_migration.new_btc_address
        _, new_address_migration = new_btc_path_migration.split(':')

        self.assertTrue(self._check_address(new_btc_path_migration, self.user1, self.new_password))

        self.assertEqual(btc_tx_migrate.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_migrate.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, edition.bitcoin_id),
                                                  (BitcoinService.minDustSize, new_address_migration)])

        self.assertEqual(btc_tx_migrate.spoolverb, 'ASCRIBESPOOL01MIGRATE{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_migrate.status, TX_PENDING)

        # check transfer
        new_btc_path_consign = ownership_consign.new_btc_address
        _, new_address_consign = new_btc_path_consign.split(':')

        self.assertEqual(btc_tx_consign.from_address, new_btc_path_migration)
        self.assertEqual(btc_tx_consign.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, new_address_consign)])

        self.assertEqual(btc_tx_consign.spoolverb, 'ASCRIBESPOOL01CONSIGN{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_consign.status, TX_PENDING)

    def test_migration_unconsign(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # reset password user2
        self.request_reset_password(self.user2)
        self.reset_password(self.user2, self.new_password)

        # create unconsign
        self.create_unconsign(self.user2, edition.bitcoin_id, self.new_password)

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_migrate = BitcoinTransaction.objects.get(ownership__type='OwnershipMigration')
        btc_tx_unconsign = BitcoinTransaction.objects.get(ownership__type='UnConsignment')
        ownership_migration = OwnershipMigration.objects.get(edition=edition)
        ownership_consign = Consignment.objects.get(edition=edition)

        # piece, editions, register, consign, migrate, unconsign
        self.assertEqual(len(btc_txs), 6)

        # check migration
        new_btc_path_migration = ownership_migration.new_btc_address
        _, new_address_migration = new_btc_path_migration.split(':')

        _, consign_address = ownership_consign.new_btc_address.split(':')

        self.assertTrue(self._check_address(new_btc_path_migration, self.user2, self.new_password))

        self.assertEqual(btc_tx_migrate.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_migrate.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, consign_address),
                                                  (BitcoinService.minDustSize, new_address_migration)])

        self.assertEqual(btc_tx_migrate.spoolverb, 'ASCRIBESPOOL01MIGRATE{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_migrate.status, TX_PENDING)

        # check unconsign
        self.assertEqual(btc_tx_unconsign.from_address, new_btc_path_migration)
        self.assertEqual(btc_tx_unconsign.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                    (BitcoinService.minDustSize, edition.bitcoin_id)])

        self.assertEqual(btc_tx_unconsign.spoolverb, 'ASCRIBESPOOL01UNCONSIGN{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_unconsign.status, TX_PENDING)

    def test_migration_loan_edition_before_password_change(self):
        # If the loan is created before the password change there will be no migration because the correct
        # wif was stored

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)
        edition = editions[0]
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=startdate,
                                 enddate=enddate, password=self.password)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm loan
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)

        self.assertFalse(OwnershipMigration.objects.filter(edition=edition).exists())

    def test_migration_loan_edition_after_password_change(self):
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

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_migrate = BitcoinTransaction.objects.get(ownership__type='OwnershipMigration')
        btc_tx_loan = BitcoinTransaction.objects.get(ownership__type='Loan')
        ownership_migration = OwnershipMigration.objects.get(edition=edition)
        ownership_loan = Loan.objects.get(edition=edition)

        # piece, editions, register, migration, loan
        self.assertEqual(len(btc_txs), 5)

        # check migration
        new_btc_path_migration = ownership_migration.new_btc_address
        _, new_address_migration = new_btc_path_migration.split(':')

        self.assertTrue(self._check_address(new_btc_path_migration, self.user1, self.new_password))

        self.assertEqual(btc_tx_migrate.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_migrate.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, edition.bitcoin_id),
                                                  (BitcoinService.minDustSize, new_address_migration)])

        self.assertEqual(btc_tx_migrate.spoolverb, 'ASCRIBESPOOL01MIGRATE{}'.format(edition.edition_number))
        self.assertEqual(btc_tx_migrate.status, TX_PENDING)

        # check loan
        new_btc_path_loan = ownership_loan.new_btc_address
        _, new_address_loan = new_btc_path_loan.split(':')

        self.assertEqual(btc_tx_loan.from_address, new_btc_path_migration)
        self.assertEqual(btc_tx_loan.outputs, [(BitcoinService.minDustSize, edition.hash_as_address_no_metada()),
                                               (BitcoinService.minDustSize, new_address_loan)])

        self.assertEqual(btc_tx_loan.spoolverb, 'ASCRIBESPOOL01LOAN{}/{}{}'.format(edition.edition_number,
                                                                                   startdate.strftime('%y%m%d'),
                                                                                   enddate.strftime('%y%m%d')))
        self.assertEqual(btc_tx_loan.status, TX_PENDING)

    def test_migration_loan_piece_before_password_change(self):
        # If the loan is created before the password change there will be no migration because the correct
        # wif was stored

        # create loan
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=startdate,
                               enddate=enddate, password=self.password)

        # change password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # confirm loan
        self.confirm_loan_piece(self.user2, piece.id)

        self.assertFalse(OwnershipMigration.objects.filter(piece=piece).exists())

    def test_migration_loan_piece_after_password_change(self):
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

        btc_txs = BitcoinTransaction.objects.filter(ownership__piece=piece)
        btc_tx_migrate = BitcoinTransaction.objects.get(ownership__type='OwnershipMigration')
        btc_tx_loan = BitcoinTransaction.objects.get(ownership__type='LoanPiece')
        ownership_migration = OwnershipMigration.objects.get(piece=piece)
        ownership_loan = LoanPiece.objects.get(piece=piece)

        # piece, migrate, loan
        self.assertEqual(len(btc_txs), 3)

        # check migration
        new_btc_path_migration = ownership_migration.new_btc_address
        _, new_address_migration = new_btc_path_migration.split(':')

        self.assertTrue(self._check_address(new_btc_path_migration, self.user1, self.new_password))

        self.assertEqual(btc_tx_migrate.from_address, BitcoinWallet.mainAdminBtcAddress())
        self.assertEqual(btc_tx_migrate.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                                  (BitcoinService.minDustSize, piece.bitcoin_id),
                                                  (BitcoinService.minDustSize, new_address_migration)])

        self.assertEqual(btc_tx_migrate.spoolverb, 'ASCRIBESPOOL01MIGRATE')
        self.assertEqual(btc_tx_migrate.status, TX_PENDING)

        # check loan
        new_btc_path_loan = ownership_loan.new_btc_address
        _, new_address_loan = new_btc_path_loan.split(':')

        self.assertEqual(btc_tx_loan.from_address, new_btc_path_migration)
        self.assertEqual(btc_tx_loan.outputs, [(BitcoinService.minDustSize, piece.hash_as_address_no_metada()),
                                               (BitcoinService.minDustSize, new_address_loan)])

        self.assertEqual(btc_tx_loan.spoolverb, 'ASCRIBESPOOL01LOAN/{}{}'.format(startdate.strftime('%y%m%d'),
                                                                                 enddate.strftime('%y%m%d')))
        self.assertEqual(btc_tx_loan.status, TX_PENDING)

    def _check_address(self, bitcoin_path, user, password):
        # check if the address belongs to the wallet with master password
        path, address = bitcoin_path.split(':')
        password = BitcoinWallet.pycoinPassword(user, password)
        return BIP32Node.from_master_secret(password, netcode='XTN').subkey_for_path(path).address() == address
