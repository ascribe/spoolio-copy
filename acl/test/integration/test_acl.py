from datetime import datetime, timedelta

from django.conf import settings

from ownership.test.util import APIUtilLoanPiece, APIUtilTransfer, APIUtilConsign
from ownership.test.util import APIUtilUnconsign, APIUtilLoanEdition, APIUtilShareEdition, APIUtilSharePiece
from ownership.models import OwnershipTransfer
from acl.models import ActionControl
from acl.test.util import APIUtilActionControl
from users.test.util import APIUtilUsers
from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from piece.test.util import APIUtilPiece
from s3.test.mocks import MockAwsTestCase


class RegisterPieceAclTest(MockAwsTestCase,
                           APIUtilUsers,
                           APIUtilDigitalWork,
                           APIUtilThumbnail,
                           APIUtilPiece,
                           APIUtilActionControl):
    fixtures = ['licenses.json']

    def setUp(self):
        super(RegisterPieceAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=0)

    def testPieceBeforeEditionsAcl(self):
        acl_piece_before_editions = ActionControl.objects.get(user=self.user1, piece=self.piece_user1, edition=None)
        self.assertTrue(self.is_piece_registree_before_editions(acl_piece_before_editions))

    def testPieceAfterEditionsAcl(self):
        self.create_editions(self.user1, self.piece_user1, 2)

        acl_piece_after_editions = ActionControl.objects.get(user=self.user1, piece=self.piece_user1, edition=None)
        self.assertTrue(self.is_piece_registree_after_editions(acl_piece_after_editions))


class RegisterEditionAclTest(MockAwsTestCase,
                             APIUtilUsers,
                             APIUtilDigitalWork,
                             APIUtilThumbnail,
                             APIUtilPiece,
                             APIUtilActionControl):
    fixtures = ['licenses.json']

    def setUp(self):
        super(RegisterEditionAclTest, self).setUp()
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

    def testEditionAcl(self):
        edition = self.editions_user1[0]
        acl_edition_registree = ActionControl.objects.get(user=self.user1, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_registree(acl_edition_registree))


class TransferEditionAclTest(MockAwsTestCase,
                             APIUtilUsers,
                             APIUtilDigitalWork,
                             APIUtilThumbnail,
                             APIUtilPiece,
                             APIUtilActionControl,
                             APIUtilTransfer):
    fixtures = ['licenses.json']

    # cases:
    # 1. transfer to unexisting user
    # 2. transfer to existing user
    # 3. withdraw transfer

    def setUp(self):
        super(TransferEditionAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testEditionTransferAcl(self):
        edition = self.editions_user1[0]
        self.create_transfer(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        acl_transferee = ActionControl.objects.get(edition=edition, user=self.user2)
        acl_prev_owner = ActionControl.objects.get(edition=edition, user=self.user1)

        self.assertTrue(self.is_edition_transferee(acl_transferee))
        self.assertTrue(self.is_edition_prev_owner(acl_prev_owner))

    def testEditionTransferToUserNeedsToRegisterAcl(self):
        edition = self.editions_user1[0]
        self.create_transfer(self.user1, self.user_needs_to_register.email, edition.bitcoin_id, self.password)

        acl_prev_owner = ActionControl.objects.get(piece=edition.parent, user=self.user1, edition=edition)
        self.assertTrue(self.is_edition_prev_owner_user_needs_to_register(acl_prev_owner))

    def testEditionTransferWithdrawAcl(self):
        edition = self.editions_user1[0]
        self.create_transfer(self.user1, self.user_needs_to_register.email, edition.bitcoin_id, self.password)
        OwnershipTransfer.objects.get(prev_owner=self.user1, new_owner=self.user_needs_to_register,
                                      edition=edition)
        self.withdraw_transfer(self.user1, edition.bitcoin_id)

        acl_prev_owner = ActionControl.objects.get(edition=edition, user=self.user1)
        self.assertTrue(self.is_edition_transferee(acl_prev_owner))

        acl_transferee = ActionControl.objects.filter(user=self.user_needs_to_register, piece=edition.parent,
                                                      edition=edition)
        self.assertEqual(len(acl_transferee), 0)


class ConsignEditionAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                            APIUtilPiece, APIUtilActionControl, APIUtilConsign):
    fixtures = ['licenses.json']

    def setUp(self):
        super(ConsignEditionAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testEditionConsignAcl(self):
        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        acl_consign_owner = ActionControl.objects.get(user=self.user1, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_consign_owner(acl_consign_owner))

        acl_consignee = ActionControl.objects.get(user=self.user2, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_consignee(acl_consignee))

    def testEditionConsignConfirmAcl(self):
        # first create consign
        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)
        acl_consign_owner = ActionControl.objects.get(user=self.user1, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_consign_owner_after_confirm(acl_consign_owner))

        acl_consign_consignee = ActionControl.objects.get(user=self.user2, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_consignee_after_confirm(acl_consign_consignee))

    def testEditionConsignDenyAcl(self):
        # first create consign
        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # deny consign
        self.deny_consign(self.user2, edition.bitcoin_id)
        acl_consign_owner = ActionControl.objects.get(user=self.user1, edition=edition)
        self.assertTrue(self.is_edition_transferee(acl_consign_owner))

        acl_consignee = ActionControl.objects.filter(user=self.user2, piece=edition.parent, edition=edition)
        self.assertEqual(len(acl_consignee), 0)

    def testEditionConsignWithdrawAcl(self):
        # first create consign
        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # withdraw consign
        self.withdraw_consign(self.user1, edition.bitcoin_id)
        acl_consign_owner = ActionControl.objects.get(user=self.user1, edition=edition)
        self.assertTrue(self.is_edition_transferee(acl_consign_owner))

        acl_consignee = ActionControl.objects.filter(user=self.user2, piece=edition.parent, edition=edition)
        self.assertEqual(len(acl_consignee), 0)


class UnConsignEditionAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                              APIUtilPiece, APIUtilActionControl, APIUtilConsign, APIUtilUnconsign):
    fixtures = ['licenses.json']

    def setUp(self):
        super(UnConsignEditionAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testEditionUnconsignAcl(self):
        # first create consign
        edition = self.editions_user1[0]
        self.create_consign(self.user1, self.user2.email, edition.bitcoin_id, self.password)

        # second confirm consign
        self.confirm_consign(self.user2, edition.bitcoin_id)

        # unconsign
        self.create_unconsign(self.user2, edition.bitcoin_id, self.password)

        acl_consign_owner = ActionControl.objects.get(user=self.user1, edition=edition)
        self.assertTrue(self.is_edition_transferee(acl_consign_owner))

        acl_consignee = ActionControl.objects.filter(user=self.user2, piece=edition.parent, edition=edition)
        self.assertEqual(len(acl_consignee), 0)


class LoanEditionAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                         APIUtilPiece, APIUtilActionControl, APIUtilLoanEdition):
    fixtures = ['licenses.json']

    def setUp(self):
        super(LoanEditionAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testEditionLoanCreateAcl(self):
        edition = self.editions_user1[0]

        self.create_loan_edition(self.user1, self.user2.email, edition.bitcoin_id,
                                 startdate=datetime.utcnow().date(),
                                 enddate=datetime.utcnow().date() + timedelta(days=1),
                                 password=self.password)

        acl_loanee = ActionControl.objects.get(edition=edition, user=self.user2)
        self.assertTrue(self.is_edition_acl_sharee(acl_loanee))


class LoanPieceAclTest(MockAwsTestCase, APIUtilLoanPiece, APIUtilUsers, APIUtilDigitalWork,
                       APIUtilThumbnail, APIUtilPiece, APIUtilActionControl):
    fixtures = ['licenses.json']

    def setUp(self):
        super(LoanPieceAclTest, self).setUp()
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

    def testAclLoanConfirm(self):
        self.create_loan_piece(self.user1, self.user2.email, self.piece_user1.id,
                               startdate=datetime.utcnow().date(),
                               enddate=datetime.utcnow().date() + timedelta(days=1),
                               password=self.password)

        acl_loanee = ActionControl.objects.get(piece=self.piece_user1, user=self.user2, edition=None)
        acl_loaner = ActionControl.objects.get(piece=self.piece_user1, user=self.user1, edition=None)

        # check acls after creating loan
        self.assertTrue(self.is_piece_sharee(acl_loanee))
        self.assertTrue(self.is_piece_registree_after_editions(acl_loaner))

        # check acls after confirm loan
        self.confirm_loan_piece(self.user2, self.piece_user1.id)
        acl_loanee = ActionControl.objects.get(piece=self.piece_user1, user=self.user2, edition=None)
        acl_loaner = ActionControl.objects.get(piece=self.piece_user1, user=self.user1, edition=None)

        self.assertTrue(self.is_piece_sharee(acl_loanee))
        self.assertTrue(self.is_piece_registree_after_editions(acl_loaner))

    def testAclLoanDeny(self):
        self.create_loan_piece(self.user1, self.user2.email, self.piece_user1.id,
                               startdate=datetime.utcnow().date(),
                               enddate=datetime.utcnow().date() + timedelta(days=1),
                               password=self.password)

        # check acls after confirm loan
        self.deny_loan_piece(self.user2, self.piece_user1.id)
        acl_loanee = ActionControl.objects.get(piece=self.piece_user1, user=self.user2, edition=None)
        acl_loaner = ActionControl.objects.get(piece=self.piece_user1, user=self.user1, edition=None)

        self.assertTrue(self.is_piece_sharee(acl_loanee))
        self.assertTrue(self.is_piece_registree_after_editions(acl_loaner))


class ShareEditionAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                          APIUtilPiece, APIUtilActionControl, APIUtilShareEdition):
    fixtures = ['licenses.json']

    def setUp(self):
        super(ShareEditionAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testShareEditionCreateAcl(self):
        edition = self.editions_user1[0]

        self.create_share_edition(self.user1, self.user2.email, edition.bitcoin_id)

        acl_sharee = ActionControl.objects.get(edition=edition, user=self.user2)
        self.assertTrue(self.is_edition_acl_sharee(acl_sharee))

    def testShareEditionDeleteAcl(self):
        edition = self.editions_user1[0]

        # first create share
        self.create_share_edition(self.user1, self.user2.email, edition.bitcoin_id)

        # delete share
        self.delete_share_edition(self.user2, edition.bitcoin_id)

        acl_sharee = ActionControl.objects.get(user=self.user2, edition=edition, piece=edition.parent)
        self.assertTrue(self.is_edition_acl_sharee_after_delete(acl_sharee))


class SharePieceAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                        APIUtilPiece, APIUtilActionControl, APIUtilSharePiece):
    fixtures = ['licenses.json']

    def setUp(self):
        super(SharePieceAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testSharePieceCreateAcl(self):
        piece = self.piece_user1

        self.create_share_piece(self.user1, self.user2.email, piece.id)

        acl_sharee = ActionControl.objects.get(user=self.user2, piece=piece, edition=None)
        self.assertTrue(self.is_piece_sharee(acl_sharee))

    def testSharePieceDeleteAcl(self):
        piece = self.piece_user1

        # first create share
        self.create_share_piece(self.user1, self.user2.email, piece.id)

        # delete share
        self.delete_share_piece(self.user2, piece.id)

        acl_sharee = ActionControl.objects.get(user=self.user2, piece=piece, edition=None)
        self.assertTrue(self.is_piece_acl_sharee_after_delete(acl_sharee))


class EditionDeleteAclTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail,
                           APIUtilPiece, APIUtilActionControl):
    fixtures = ['licenses.json']

    def setUp(self):
        super(EditionDeleteAclTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user_needs_to_register = self.create_user_needs_to_register('user3@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)

    def testEditionDeleteAcl(self):
        edition = self.editions_user1[0]

        self.delete_edition(self.user1, edition.bitcoin_id)

        acl_registree = ActionControl.objects.get(user=self.user1, piece=edition.parent, edition=edition)
        self.assertTrue(self.is_edition_registree_after_delete(acl_registree))
