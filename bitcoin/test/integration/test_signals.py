from mock import MagicMock

from datetime import datetime, timedelta

from django.conf import settings
from django.db.models.signals import post_save


from piece.test.util import APIUtilPiece
from blobs.test.util import APIUtilThumbnail, APIUtilDigitalWork
from ownership.models import OwnershipPiece, Ownership, OwnershipEditions, OwnershipTransfer
from ownership.models import Consignment, UnConsignment, Loan, LoanPiece, ConsignedRegistration, OwnershipMigration
from ownership import signals as ownership_signals
from ownership.api import TransferEndpoint, ConsignEndpoint, UnConsignEndpoint, LoanEndpoint, LoanPieceEndpoint
from ownership.test.util import APIUtilTransfer, APIUtilConsign, APIUtilUnconsign, APIUtilLoanEdition, APIUtilLoanPiece
from s3.test.mocks import MockAwsTestCase
from users.test.util import APIUtilUsers
from users.signals import check_pending_actions
from users.api import UserEndpoint


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


class BitcoinSignalReceiversTestCase(MockAwsTestCase,
                                     APIUtilUsers,
                                     APIUtilThumbnail,
                                     APIUtilDigitalWork,
                                     APIUtilPiece,
                                     APIUtilTransfer,
                                     APIUtilConsign,
                                     APIUtilUnconsign,
                                     APIUtilLoanEdition,
                                     APIUtilLoanPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        super(BitcoinSignalReceiversTestCase, self).setUp()
        self.password = '0' * 10
        self.new_password = '1' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        # delete ownership
        Ownership.objects.all().delete()

    def test_register_piece_no_editions(self):
        handler_piece = MagicMock()
        handler_edition = MagicMock()
        post_save.connect(handler_piece, sender=OwnershipPiece)
        post_save.connect(handler_edition, sender=OwnershipEditions)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)

        ownership = OwnershipPiece.objects.get(piece=piece)
        handler_piece.assert_called_with(created=True, instance=ownership, raw=False, sender=OwnershipPiece,
                                         signal=post_save, update_fields=None, using='default')
        self.assertFalse(handler_edition.called)

    def test_register_piece_with_editions(self):
        handler_piece = MagicMock()
        handler_edition = MagicMock()
        post_save.connect(handler_piece, sender=OwnershipPiece)
        post_save.connect(handler_edition, sender=OwnershipEditions)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=10)

        ownership_piece = OwnershipPiece.objects.get(piece=piece)
        ownership_edition = OwnershipEditions.objects.get(piece=piece)

        handler_piece.assert_called_with(created=True, instance=ownership_piece, raw=False, sender=OwnershipPiece,
                                         signal=post_save, update_fields=None, using='default')

        handler_edition.assert_called_with(created=True, instance=ownership_edition, raw=False,
                                           sender=OwnershipEditions, signal=post_save,
                                           update_fields=None, using='default')

    def test_register_number_editions(self):
        handler_edition = MagicMock()
        post_save.connect(handler_edition, sender=OwnershipEditions)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.create_editions(self.user1, piece, 10)
        ownership_edition = OwnershipEditions.objects.get(piece=piece)

        handler_edition.assert_called_with(created=True, instance=ownership_edition, raw=False,
                                           sender=OwnershipEditions, signal=post_save,
                                           update_fields=None, using='default')

    def test_consigned_registration(self):
        handler_consigned = MagicMock()
        post_save.connect(handler_consigned, sender=ConsignedRegistration)

        piece, editions = self.create_consigned_registration(self.user1, self.digitalwork_user1,
                                                             self.thumbnail_user1, num_editions=2)
        ownership_consigned = ConsignedRegistration.objects.get(piece=piece)

        handler_consigned.assert_called_with(created=True, instance=ownership_consigned, raw=False,
                                             sender=ConsignedRegistration, signal=post_save,
                                             update_fields=None, using='default')

    def test_transfer_edition(self):
        handler_transfer = MagicMock()
        ownership_signals.transfer_created.connect(handler_transfer, sender=TransferEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        ownership_transfer = OwnershipTransfer.objects.get(edition=edition)

        handler_transfer.assert_called_with(instance=ownership_transfer, password=self.password,
                                            sender=TransferEndpoint, signal=ownership_signals.transfer_created)

    def test_create_consignment(self):
        handler_consign = MagicMock()
        ownership_signals.consignment_created.connect(handler_consign, sender=ConsignEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        ownership_consign = Consignment.objects.get(edition=edition)

        handler_consign.assert_called_with(instance=ownership_consign, password=self.password,
                                           sender=ConsignEndpoint, signal=ownership_signals.consignment_created)

    def test_confirm_consignment(self):
        handler_consign_confirm = MagicMock()
        ownership_signals.consignment_confirmed.connect(handler_consign_confirm, sender=ConsignEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        self.confirm_consign(self.user2, edition.bitcoin_id)
        ownership_consign = Consignment.objects.get(edition=edition)

        handler_consign_confirm.assert_called_with(instance=ownership_consign, sender=ConsignEndpoint,
                                                   signal=ownership_signals.consignment_confirmed)

    def test_unconsignment(self):
        handler_unconsign = MagicMock()
        ownership_signals.unconsignment_create.connect(handler_unconsign, sender=UnConsignEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        self.confirm_consign(self.user2, edition)
        self.create_unconsign(self.user2, edition.bitcoin_id, self.password)
        ownership_unconsign = UnConsignment.objects.get(edition=edition)

        handler_unconsign.assert_called_with(instance=ownership_unconsign, password=self.password,
                                             sender=UnConsignEndpoint, signal=ownership_signals.unconsignment_create)

    def test_create_loan_edition(self):
        handler_loan_edition = MagicMock()
        ownership_signals.loan_edition_created.connect(handler_loan_edition, sender=LoanEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id,
                                 datetime.utcnow().date(), datetime.utcnow().date() + timedelta(days=1), self.password)
        ownership_loan = Loan.objects.get(edition=edition)

        handler_loan_edition.assert_called_with(instance=ownership_loan, password=self.password,
                                                sender=LoanEndpoint, signal=ownership_signals.loan_edition_created)

    def test_confirm_loan_edition(self):
        handler_loan_edition_confirm = MagicMock()
        ownership_signals.loan_edition_confirm.connect(handler_loan_edition_confirm, sender=LoanEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id,
                                 datetime.utcnow().date(), datetime.utcnow().date() + timedelta(days=1), self.password)
        self.confirm_loan_edition(self.user2, edition.bitcoin_id)
        ownership_loan = Loan.objects.get(edition=edition)

        handler_loan_edition_confirm.assert_called_with(instance=ownership_loan, sender=LoanEndpoint,
                                                        signal=ownership_signals.loan_edition_confirm)

    def test_create_loan_piece(self):
        handler_loan_piece = MagicMock()
        ownership_signals.loan_piece_created.connect(handler_loan_piece, sender=LoanPieceEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, datetime.utcnow().date(),
                               datetime.utcnow().date() + timedelta(days=1), self.password)
        ownership_loan_piece = LoanPiece.objects.get(piece=piece)

        handler_loan_piece.assert_called_with(instance=ownership_loan_piece, password=self.password,
                                              sender=LoanPieceEndpoint, signal=ownership_signals.loan_piece_created)

    def test_confirm_loan_piece(self):
        handler_loan_piece_confirm = MagicMock()
        ownership_signals.loan_piece_confirm.connect(handler_loan_piece_confirm, sender=LoanPieceEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.create_loan_piece(self.user1, self.user2.email, piece.id, datetime.utcnow().date(),
                               datetime.utcnow().date() + timedelta(days=1), self.password)

        self.confirm_loan_piece(self.user2, piece.id)
        ownership_loan_piece = LoanPiece.objects.get(piece=piece)

        handler_loan_piece_confirm.assert_called_with(instance=ownership_loan_piece, sender=LoanPieceEndpoint,
                                                      signal=ownership_signals.loan_piece_confirm)

    # TODO: Check this step in the api. The problem is that at this point we do not have a password
    def test_request_loan_piece(self):
        pass

    def test_request_confirm_loan_piece(self):
        handler_loan_piece_confirm = MagicMock()
        ownership_signals.loan_piece_confirm.connect(handler_loan_piece_confirm, sender=LoanPieceEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)
        self.request_loan_piece(self.user2, piece.id, datetime.utcnow().date(),
                                datetime.utcnow().date() + timedelta(days=1))

        self.request_confirm_loan_piece(self.user1, piece.id, self.password)
        ownership_loan_piece = LoanPiece.objects.get(piece=piece)

        handler_loan_piece_confirm.assert_called_with(instance=ownership_loan_piece, sender=LoanPieceEndpoint,
                                                      signal=ownership_signals.loan_piece_confirm)

    def test_migration_transfer(self):
        handler_migration = MagicMock()
        post_save.connect(handler_migration, sender=OwnershipMigration)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]

        # reset password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)
        ownership_migration = OwnershipMigration.objects.get(edition=edition)

        handler_migration.assert_called_with(created=True, instance=ownership_migration, raw=False,
                                             sender=OwnershipMigration, signal=post_save,
                                             update_fields=None, using='default')

    def test_migration_consign(self):
        handler_migration = MagicMock()
        post_save.connect(handler_migration, sender=OwnershipMigration)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]

        # reset password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.new_password)
        ownership_migration = OwnershipMigration.objects.get(edition=edition)

        handler_migration.assert_called_with(created=True, instance=ownership_migration, raw=False,
                                             sender=OwnershipMigration, signal=post_save,
                                             update_fields=None, using='default')

    def test_migration_unconsign(self):
        handler_migration = MagicMock()
        post_save.connect(handler_migration, sender=OwnershipMigration)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]

        # consign
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)
        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # reset password
        self.request_reset_password(self.user2)
        self.reset_password(self.user2, self.new_password)

        # unconsign
        self.create_unconsign(self.user2, edition.bitcoin_id, self.new_password)
        ownership_migration = OwnershipMigration.objects.get(edition=edition)

        handler_migration.assert_called_with(created=True, instance=ownership_migration, raw=False,
                                             sender=OwnershipMigration, signal=post_save,
                                             update_fields=None, using='default')

    def test_migration_loan_edition(self):
        handler_migration = MagicMock()
        post_save.connect(handler_migration, sender=OwnershipMigration)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]

        # reset password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # loan edition
        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id, startdate=datetime.utcnow().date(),
                                 enddate=datetime.utcnow().date() + timedelta(days=1), password=self.new_password)
        ownership_migration = OwnershipMigration.objects.get(edition=edition)

        handler_migration.assert_called_with(created=True, instance=ownership_migration, raw=False,
                                             sender=OwnershipMigration, signal=post_save,
                                             update_fields=None, using='default')

    def test_migration_loan_piece(self):
        handler_migration = MagicMock()
        post_save.connect(handler_migration, sender=OwnershipMigration)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=0)

        # reset password
        self.request_reset_password(self.user1)
        self.reset_password(self.user1, self.new_password)

        # loan piece
        self.create_loan_piece(self.user1, self.user2.email, piece.id, startdate=datetime.utcnow().date(),
                               enddate=datetime.utcnow().date() + timedelta(days=1), password=self.new_password)
        ownership_migration = OwnershipMigration.objects.get(piece=piece)

        handler_migration.assert_called_with(created=True, instance=ownership_migration, raw=False,
                                             sender=OwnershipMigration, signal=post_save,
                                             update_fields=None, using='default')

    def test_execute_pending_actions(self):
        handler_pending_actions = MagicMock()
        check_pending_actions.connect(handler_pending_actions, sender=UserEndpoint)

        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]
        non_registered_email = 'user3@test.com'

        # transfer edition to non-registered user
        self.create_transfer(self.user1, non_registered_email, edition.bitcoin_id, self.password)

        # register user
        user3 = self.create_user(non_registered_email, self.password)

        handler_pending_actions.assert_called_with(sender=UserEndpoint, signal=check_pending_actions, user=user3)
