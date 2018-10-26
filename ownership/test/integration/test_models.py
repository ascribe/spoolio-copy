from datetime import timedelta
import unittest

import pytz

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.datetime_safe import datetime

from bitcoin.models import BitcoinWallet
from blobs.models import DigitalWork, Thumbnail
from blobs.models import OtherData
from dynamicfixtures import mock_s3_bucket
from piece.test.util import APIUtilPiece
from ownership.models import OwnershipRegistration, OwnershipTransfer
from ownership.models import Consignment, UnConsignment, Share, Loan, LoanDetail
from users.test.util import APIUtilUsers

__author__ = 'dimi'

FIX_URL_JPG = 'http://ascribe0.s3.amazonaws.com/media/thumbnails/ascribe_spiral.png'
FIX_KEY_PNG = 'media/thumbnails/ascribe_spiral.png'


def create_user_admin():
    password_admin = settings.DJANGO_PYCOIN_ADMIN_PASS
    user_admin = User.objects.create(username="mysite_user", email="admin@keidom.com", password=password_admin)
    BitcoinWallet.create(user_admin, password=password_admin).save()
    return user_admin, password_admin


def create_user_test():
    password_test = 'test'
    user_test = APIUtilUsers.create_user("testuser@keidom.com", password=password_test)
    return user_test, password_test


class OwnershipRegistrationTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateOwnershipRegistration(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_ownershipregistration = OwnershipRegistration.create(editions[0],
                                                                  self.user_admin)
        save_ownershipregistration.prev_btc_address = 'dsdfas'
        save_ownershipregistration.new_btc_address = 'asdsad'
        save_ownershipregistration.save()

        find_ownershipregistration = OwnershipRegistration.objects.get(id=save_ownershipregistration.id)
        compare_ownerships(self, save_ownershipregistration, find_ownershipregistration)

    @mock_s3_bucket
    def testUpdateOwnershipRegistration(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_ownershipregistration = OwnershipRegistration.create(editions[0],
                                                                  self.user_admin)
        save_ownershipregistration.prev_btc_address = 'dsdfas'
        save_ownershipregistration.new_btc_address = 'asdsad'
        save_ownershipregistration.save()

        find_ownershipregistration = OwnershipRegistration.objects.get(id=save_ownershipregistration.id)
        compare_ownerships(self, save_ownershipregistration, find_ownershipregistration)

        save_ownershipregistration.prev_btc_address = 'new_address'
        save_ownershipregistration.save()

        find_ownershipregistration = OwnershipRegistration.objects.get(id=save_ownershipregistration.id)
        compare_ownerships(self, save_ownershipregistration, find_ownershipregistration)
        self.assertEqual(find_ownershipregistration.prev_btc_address, 'new_address')


class ConsignmentTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateConsignment(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_consignment = Consignment.create(editions[0],
                                              self.user_admin,
                                              owner=editions[0].owner)
        save_consignment.prev_btc_address = 'dsdfas'
        save_consignment.new_btc_address = 'asdsad'
        save_consignment.save()

        find_consignment = Consignment.objects.get(id=save_consignment.id)
        compare_ownerships(self, save_consignment, find_consignment)

    @mock_s3_bucket
    def testUpdateConsignment(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_consignment = Consignment.create(editions[0],
                                              self.user_admin,
                                              owner=editions[0].owner)
        save_consignment.prev_btc_address = 'dsdfas'
        save_consignment.new_btc_address = 'asdsad'
        save_consignment.save()

        find_consignment = Consignment.objects.get(id=save_consignment.id)
        compare_ownerships(self, save_consignment, find_consignment)

        save_consignment.new_btc_address = 'new_address'
        save_consignment.save()

        find_consignment = Consignment.objects.get(id=save_consignment.id)
        compare_ownerships(self, save_consignment, find_consignment)
        self.assertEqual(find_consignment.new_btc_address, 'new_address')


class UnConsignmentTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateUnConsignment(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        # we need to create a consignment before we can create an unconsignment
        save_consignment = Consignment.create(editions[0],
                                              self.user_admin,
                                              owner=editions[0].owner)
        save_consignment.prev_btc_address = 'dsdfas'
        save_consignment.new_btc_address = 'asdsad'
        save_consignment.save()

        save_unconsignment = UnConsignment.create(editions[0],
                                                  self.user_admin,
                                                  owner=editions[0].owner)
        save_unconsignment.prev_btc_address = 'dsdfas'
        save_unconsignment.new_btc_address = 'asdsad'
        save_unconsignment.save()

        find_unconsignment = UnConsignment.objects.get(id=save_unconsignment.id)
        compare_ownerships(self, save_unconsignment, find_unconsignment)

    @mock_s3_bucket
    def testUpdateUnConsignment(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        # we need to create a consignment before we can create an unconsignment
        save_consignment = Consignment.create(editions[0],
                                              self.user_admin,
                                              owner=editions[0].owner)
        save_consignment.prev_btc_address = 'dsdfas'
        save_consignment.new_btc_address = 'asdsad'
        save_consignment.save()

        save_unconsignment = UnConsignment.create(editions[0],
                                                  consignee=self.user_admin,
                                                  owner=editions[0].owner)
        save_unconsignment.prev_btc_address = 'dsdfas'
        save_unconsignment.new_btc_address = 'asdsad'
        save_unconsignment.save()

        find_unconsignment = UnConsignment.objects.get(id=save_unconsignment.id)
        compare_ownerships(self, save_unconsignment, find_unconsignment)

        save_unconsignment.new_btc_address = 'new_address'
        save_unconsignment.save()

        find_unconsignment = UnConsignment.objects.get(id=save_unconsignment.id)
        compare_ownerships(self, save_unconsignment, find_unconsignment)
        self.assertEqual(find_unconsignment.new_btc_address, 'new_address')


class OwnershipTransferTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateOwnershipTransfer(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_ownershiptransfer = OwnershipTransfer.create(editions[0],
                                                          self.user_admin,
                                                          prev_owner=editions[0].owner)
        save_ownershiptransfer.prev_btc_address = 'dsd'
        save_ownershiptransfer.new_btc_address = 'qsq'

        save_ownershiptransfer.save()

        find_ownershiptransfer = OwnershipTransfer.objects.get(id=save_ownershiptransfer.id)
        compare_ownerships(self, save_ownershiptransfer, find_ownershiptransfer)

    @mock_s3_bucket
    def testUpdateOwnershipTransfer(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_ownershiptransfer = OwnershipTransfer.create(editions[0],
                                                          self.user_admin,
                                                          prev_owner=editions[0].owner)
        save_ownershiptransfer.prev_btc_address = 'dsd'
        save_ownershiptransfer.new_btc_address = 'qsq'
        save_ownershiptransfer.ciphertext_wif = 'cipher'
        save_ownershiptransfer.save()

        find_ownershiptransfer = OwnershipTransfer.objects.get(id=save_ownershiptransfer.id)
        compare_ownerships(self, save_ownershiptransfer, find_ownershiptransfer)

        save_ownershiptransfer.new_btc_address = 'new_address'
        save_ownershiptransfer.ciphertext_wif = 'new_cipher'

        save_ownershiptransfer.save()

        find_ownershiptransfer = OwnershipTransfer.objects.get(id=save_ownershiptransfer.id)
        compare_ownerships(self, save_ownershiptransfer, find_ownershiptransfer)
        self.assertEqual(find_ownershiptransfer.new_btc_address, 'new_address')
        self.assertNotEqual(find_ownershiptransfer.ciphertext_wif, None)

    @mock_s3_bucket
    def testDate(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_ownershiptransfer = OwnershipTransfer.create(editions[0],
                                                          self.user_admin,
                                                          prev_owner=editions[0].owner)
        save_ownershiptransfer.prev_btc_address = 'dsd'
        save_ownershiptransfer.new_btc_address = 'qsq'
        save_ownershiptransfer.ciphertext_wif = 'cipher'

        save_ownershiptransfer.save()

        find_ownershiptransfer = OwnershipTransfer.objects.get(id=save_ownershiptransfer.id)
        compare_ownerships(self, save_ownershiptransfer, find_ownershiptransfer)

        save_ownershiptransfer.new_btc_address = 'new_address'
        save_ownershiptransfer.save()

        find_ownershiptransfer = OwnershipTransfer.objects.get(id=save_ownershiptransfer.id)
        compare_ownerships(self, save_ownershiptransfer, find_ownershiptransfer)
        self.assertEqual(find_ownershiptransfer.new_btc_address, 'new_address')
        self.assertNotEqual(find_ownershiptransfer.ciphertext_wif, None)


class ShareTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateShare(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_share = Share.create(editions[0],
                                  self.user_admin)

        save_share.save()

        find_share = Share.objects.get(id=save_share.id)
        compare_ownerships(self, save_share, find_share)

    @mock_s3_bucket
    def testUpdateShare(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_share = Share.create(editions[0],
                                  self.user_admin)

        save_share.save()

        find_share = Share.objects.get(id=save_share.id)
        compare_ownerships(self, save_share, find_share)

        save_share.shared_user = user
        save_share.save()

        find_share = Share.objects.get(id=save_share.id)
        compare_ownerships(self, save_share, find_share)
        self.assertEqual(find_share.shared_user.username, user.username)


class LoanTestCase(TestCase):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        (self.user_admin, self.password_admin) = create_user_admin()
        (self.user_test, self.password_test) = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    @mock_s3_bucket
    def testCreateLoan(self):
        from ..models import Contract
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_loan = Loan.create(editions[0],
                                self.user_admin,
                                owner=editions[0].owner)
        save_loan.prev_btc_address = 'dsdfas'
        save_loan.new_btc_address = 'asdsad'
        save_loan.datetime_from = datetime.combine(self.date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        save_loan.datetime_to = datetime.combine(self.date, datetime.min.time()).replace(tzinfo=pytz.UTC)

        save_loan.save()
        save_file = OtherData.objects.create(user=self.user_test, key=FIX_KEY_PNG)
        contract = Contract.objects.create(issuer=self.user_test, blob=save_file)
        loan_details = LoanDetail(loan=save_loan,
                                  gallery="gallery",
                                  contract_model=contract)
        loan_details.save()

        find_loan = Loan.objects.get(id=save_loan.id)
        compare_ownerships(self, save_loan, find_loan)
        compare_loan_details(self, save_loan.details, find_loan.details)
        self.assertEqual(save_loan.details.contract_model.blob.key, FIX_KEY_PNG)

    @mock_s3_bucket
    def testUpdateLoan(self):
        """
        """
        user = self.user_test

        digital_work = DigitalWork(user=self.user_test,
                                   digital_work_file=FIX_URL_JPG,
                                   digital_work_hash='hash')
        digital_work.save()

        thumbnail = Thumbnail(user=self.user_test, key=FIX_URL_JPG)
        thumbnail.save()

        root_piece, editions = APIUtilPiece.create_piece(user,
                                                         title='title',
                                                         artist_name='artist_name',
                                                         num_editions=2,
                                                         thumbnail=thumbnail,
                                                         digital_work=digital_work)

        save_loan = Loan.create(editions[0],
                                self.user_admin,
                                owner=editions[0].owner)
        save_loan.prev_btc_address = 'dsdfas'
        save_loan.new_btc_address = 'asdsad'
        save_loan.save()

        find_loan = Loan.objects.get(id=save_loan.id)
        compare_ownerships(self, save_loan, find_loan)

        save_loan.new_btc_address = 'new_address'
        save_loan.save()

        find_loan = Loan.objects.get(id=save_loan.id)
        compare_ownerships(self, save_loan, find_loan)
        self.assertEqual(find_loan.new_btc_address, 'new_address')


class ContractTestCase(TestCase):
    def test_create_contract_without_fields(self):
        from ..models import Contract
        with self.assertRaises(IntegrityError):
            Contract.objects.create()

    def tesi_create_contract_without_issuer(self):
        from ..models import Contract
        with self.assertRaises(IntegrityError) as e:
            Contract.objects.create()
        self.assertIn(
            'null value in column "issuer_id" violates not-null constraint\n',
            e.exception.message
        )

    def test_create_contract_without_blob(self):
        from ..models import Contract
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        with self.assertRaises(IntegrityError) as e:
            Contract.objects.create(issuer=issuer)
        self.assertIn(
            'null value in column "blob_id" violates not-null constraint\n',
            e.exception.message
        )

    def test_create_contract_default(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        self.assertTrue(hasattr(contract, 'datetime_created'))
        self.assertTrue(hasattr(contract, 'issuer'))
        self.assertTrue(hasattr(contract, 'blob'))
        self.assertTrue(hasattr(contract, 'name'))
        self.assertTrue(hasattr(contract, 'is_active'))
        self.assertTrue(hasattr(contract, 'is_public'))
        self.assertEqual(contract.issuer, issuer)
        self.assertEqual(contract.blob, blob)
        self.assertEqual(contract.name, '')
        self.assertEqual(contract.is_active, True)
        self.assertEqual(contract.is_public, False)

    def test_create_contract_with_name(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(
            issuer=issuer, blob=blob, name='awesome_deal')
        self.assertEqual(contract.name, 'awesome_deal')

    def test_create_many_contracts_with_same_name_for_same_issuer(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        Contract.objects.create(issuer=issuer, blob=blob, name='awesome_deal')
        Contract.objects.create(issuer=issuer, blob=blob, name='awesome_deal')
        self.assertEqual(Contract.objects.count(), 2)

    def test_active_contract_uniqueness_upon_creation(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        c1 = Contract.objects.create(issuer=issuer, blob=blob, name='abc')
        c2 = Contract.objects.create(issuer=issuer, blob=blob, name='abc')
        self.assertFalse(Contract.objects.get(pk=c1.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=c2.pk).is_active)

    def test_active_contract_uniqueness_upon_save(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        c1 = Contract.objects.create(
            issuer=issuer, blob=blob, name='abc', is_active=True)
        c2 = Contract.objects.create(
            issuer=issuer, blob=blob, name='abc', is_active=False)
        c2.is_active = True
        c2.save()
        self.assertFalse(Contract.objects.get(pk=c1.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=c2.pk).is_active)

    def test_private_contract_deactivation(self):
        """
        The case:
            Consider issuer "merlin", with an existing active/private contract,
            named 'magic'. A new contract is then issued for merlin, with the
            same name, "magic", and is this time public and active.

            The expected outcome is that the new contract will "deactivate" the
            older one. In other words: ``old_contract.is_active == True``.

        """
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        merlin = User.objects.create(username='merlin', email='merlin@abc.io')
        blob = OtherData.objects.create(user=merlin, key='key')
        old_contract = Contract.objects.create(
            is_active=True,
            is_public=False,
            name='magic',
            issuer=merlin,
            blob=blob
        )
        new_contract = Contract.objects.create(
            is_active=True,
            is_public=True,
            name='magic',
            issuer=merlin,
            blob=blob
        )
        self.assertFalse(Contract.objects.get(pk=old_contract.pk).is_active)
        self.assertFalse(Contract.objects.get(pk=old_contract.pk).is_public)
        self.assertTrue(Contract.objects.get(pk=new_contract.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=new_contract.pk).is_public)

    @unittest.skip('not implemented')
    def test_active_contract_uniqueness_upon_bulk_create(self):
        """
        Overridden model methods are not called on bulk operations

        """
        raise NotImplementedError

    @unittest.skip('not implemented')
    def test_active_contract_uniqueness_upon_bulk_update(self):
        """
        Overridden model methods are not called on bulk operations

        """
        raise NotImplementedError

    def test_create_multiple_contracts_with_same_name_for_diff_issuers(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        merlin = User.objects.create(username='merlin', email='merlin@abc.io')
        chuck = User.objects.create(username='chuck', email='chuck@abc.io')
        blob = OtherData.objects.create()
        Contract.objects.create(issuer=merlin, blob=blob, name='aswesome_deal')
        Contract.objects.create(issuer=chuck, blob=blob, name='aswesome_deal')

    # TODO move test into ContractAgreementTestCase
    @unittest.skip('moved appendix field to ContractAgreement')
    def test_create_contract_with_appendix(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        appendix = {'rainbow': 'the sky bows to the rain'}
        contract = Contract.objects.create(
            issuer=issuer, blob=blob, appendix=appendix)
        self.assertEqual(contract.appendix, appendix)

    # TODO move test into ContractAgreementTestCase
    @unittest.skip('moved appendix field to ContractAgreement')
    def test_update_contract_appendix(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        appendix = {'rainbow': 'the sky bows to the rain'}
        contract = Contract.objects.create(
            issuer=issuer, blob=blob, appendix=appendix)
        self.assertEqual(contract.appendix, appendix)
        appendix = None
        contract.appendix = appendix
        contract.save()
        self.assertIsNone(contract.appendix)

    def test_update_contract_blob(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        self.assertEqual(contract.blob, blob)
        new_blob = OtherData.objects.create()
        contract.blob = new_blob
        contract.save()
        self.assertEqual(contract.blob, new_blob)

    def test_delete_contract(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        self.assertTrue(Contract.objects.filter(pk=contract.pk).exists())
        contract_pk = contract.pk
        contract.delete()
        self.assertFalse(Contract.objects.filter(pk=contract_pk).exists())

    def test_deactivate_contracts(self):
        from ..models import Contract
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob_0 = OtherData.objects.create(user=issuer, key='key_0')
        blob_1 = OtherData.objects.create(user=issuer, key='key_1')
        c_0 = Contract.objects.create(issuer=issuer, blob=blob_0, name='n')
        c_1 = Contract.objects.create(issuer=issuer, blob=blob_1, name='n')
        self.assertEqual(Contract.objects.count(), 2)
        self.assertFalse(Contract.objects.get(pk=c_0.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=c_1.pk).is_active)

    def test_deactivate_public_contract_with_one_contract_agreement(self):
        """
        Tests that the expected side effects of "updating" a contract happen as
        expected. The asscoiated contract agreement should be set to deleted.

        """
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        signee = User.objects.create(username='signee', email='signee@abc.io')
        blob_0 = OtherData.objects.create(user=issuer, key='key_0')
        blob_1 = OtherData.objects.create(user=issuer, key='key_1')
        c_0 = Contract.objects.create(
            issuer=issuer,
            blob=blob_0,
            name='n',
            is_public=True
        )
        ca_0 = ContractAgreement.objects.create(signee=signee, contract=c_0)
        self.assertIsNone(ca_0.datetime_deleted)
        c_1 = Contract.objects.create(issuer=issuer, blob=blob_1, name='n')
        self.assertEqual(Contract.objects.count(), 2)
        self.assertFalse(Contract.objects.get(pk=c_0.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=c_1.pk).is_active)
        c_0 = Contract.objects.get(pk=c_0.pk)
        ca_0 = c_0.contractagreement_set.get()
        self.assertIsNotNone(ca_0.datetime_deleted)
        c_1 = Contract.objects.get(pk=c_1.pk)
        self.assertFalse(c_1.contractagreement_set.exists())

    def test_deactivate_private_contract_with_one_contract_agreement(self):
        """
        Tests that the expected side effects of "updating" a contract happen as
        expected.

        """
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        signee = User.objects.create(username='signee', email='signee@abc.io')
        blob_0 = OtherData.objects.create(user=issuer, key='key_0')
        blob_1 = OtherData.objects.create(user=issuer, key='key_1')
        c_0 = Contract.objects.create(
            issuer=issuer,
            blob=blob_0,
            name='n',
            is_public=False
        )
        ca_0 = ContractAgreement.objects.create(signee=signee, contract=c_0)
        self.assertIsNone(ca_0.datetime_deleted)
        c_1 = Contract.objects.create(issuer=issuer, blob=blob_1, name='n')
        self.assertEqual(Contract.objects.count(), 2)
        self.assertFalse(Contract.objects.get(pk=c_0.pk).is_active)
        self.assertTrue(Contract.objects.get(pk=c_1.pk).is_active)
        c_0 = Contract.objects.get(pk=c_0.pk)
        ca_0 = c_0.contractagreement_set.get()
        self.assertIsNotNone(ca_0.datetime_deleted)
        c_1 = Contract.objects.get(pk=c_1.pk)
        self.assertTrue(c_1.contractagreement_set.exists())
        ca_1 = c_1.contractagreement_set.get()
        self.assertIsNone(ca_1.datetime_deleted)

    @unittest.skip('not yet implemented')
    def test_deactivate_contract_with_multiple_contract_agreements(self):
        raise NotImplementedError


class ContractAgreementTestCase(TestCase):
    def test_create_contract_agreement_without_fields(self):
        from ..models import ContractAgreement
        with self.assertRaises(Exception):
            ContractAgreement.objects.create()

    def tesi_create_contract_agreement_without_contract(self):
        from ..models import ContractAgreement
        with self.assertRaises(IntegrityError) as e:
            ContractAgreement.objects.create()
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            e.exception.message
        )

    def tesi_create_contract_agreement_without_signee(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        with self.assertRaises(IntegrityError) as e:
            ContractAgreement.objects.create(contract=contract)
        self.assertIn(
            'null value in column "signee_id" violates not-null constraint',
            e.exception.message
        )

    def test_create_contract_agreement_default(self):
        from datetime import datetime
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        contract_agreement = ContractAgreement.objects.create(contract=contract,
                                                              signee=signee)
        self.assertTrue(hasattr(contract_agreement, 'appendix'))
        self.assertTrue(hasattr(contract_agreement, 'contract'))
        self.assertTrue(hasattr(contract_agreement, 'signee'))
        self.assertTrue(hasattr(contract_agreement, 'datetime_created'))
        self.assertTrue(hasattr(contract_agreement, 'datetime_deleted'))
        self.assertTrue(hasattr(contract_agreement, 'datetime_accepted'))
        self.assertTrue(hasattr(contract_agreement, 'datetime_rejected'))
        self.assertIsNone(contract_agreement.appendix)
        self.assertEqual(contract_agreement.contract, contract)
        self.assertEqual(contract_agreement.signee, signee)
        self.assertIsNotNone(contract_agreement.datetime_created)
        self.assertTrue(
            isinstance(contract_agreement.datetime_created, datetime))
        self.assertIsNone(contract_agreement.datetime_deleted)
        self.assertIsNone(contract_agreement.datetime_accepted)
        self.assertIsNone(contract_agreement.datetime_rejected)

    def test_create_contract_agreement_with_datetime_deleted(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        datetime_deleted = datetime.utcnow().replace(tzinfo=pytz.UTC)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=signee, datetime_deleted=datetime_deleted)
        self.assertEqual(contract_agreement.datetime_deleted, datetime_deleted)

    def test_update_contract_agreement_datetime_accepted(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        datetime_deleted = datetime.utcnow().replace(tzinfo=pytz.UTC)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=signee, datetime_deleted=datetime_deleted)
        self.assertIsNone(contract_agreement.datetime_accepted)
        datetime_accepted = datetime_deleted + timedelta(days=1)
        contract_agreement.datetime_accepted = datetime_accepted
        contract_agreement.save()
        self.assertEqual(contract_agreement.datetime_accepted, datetime_accepted)

    def test_update_contract_agreement_datetime_rejected(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        contract_agreement = ContractAgreement.objects.create(
            contract=contract,
            signee=signee
        )
        self.assertIsNone(contract_agreement.datetime_rejected)
        datetime_rejected = datetime.utcnow().replace(tzinfo=pytz.UTC)
        contract_agreement.datetime_rejected = datetime_rejected
        contract_agreement.save()
        self.assertEqual(contract_agreement.datetime_rejected, datetime_rejected)

    @unittest.skip('until soft deletion logic is full implemented')
    def test_try_to_reject_soft_deleted_contract_agreement_(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        datetime_deleted = datetime.utcnow().replace(tzinfo=pytz.UTC)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract,
            signee=signee,
            datetime_deleted=datetime_deleted
        )
        self.assertIsNone(contract_agreement.datetime_rejected)
        datetime_rejected = datetime_deleted + timedelta(days=3)
        contract_agreement.datetime_rejected = datetime_rejected
        with self.assertRaises(ValidationError) as err:
            contract_agreement.save()
        self.assertEqual(err.exception.message,
                         'Cannot reject a deleted contract agreement!')
        self.assertIsNone(contract_agreement.datetime_rejected)

    def test_try_to_reject_accepted_contract_agreement(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        datetime_sent = datetime.utcnow().replace(tzinfo=pytz.UTC)
        datetime_accepted = datetime_sent + timedelta(days=1)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract,
            signee=signee,
            datetime_accepted=datetime_accepted
        )
        self.assertIsNone(contract_agreement.datetime_rejected)
        datetime_rejected = datetime_sent + timedelta(days=3)
        contract_agreement.datetime_rejected = datetime_rejected
        with self.assertRaises(ValidationError) as err:
            contract_agreement.save()
        self.assertEqual(err.exception.message,
                         'Cannot reject an accepted contract agreement!')
        self.assertIsNone(err.exception.code)
        contract_agreement = ContractAgreement.objects.get(pk=contract_agreement.pk)
        self.assertIsNone(contract_agreement.datetime_rejected)

    def test_delete_contract_agreement(self):
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        from users.models import User
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        datetime_deleted = datetime.utcnow().replace(tzinfo=pytz.UTC)
        datetime_accepted = datetime_deleted + timedelta(days=1)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract,
            signee=signee,
            datetime_deleted=datetime_deleted,
            datetime_accepted=datetime_accepted,
        )
        self.assertTrue(
            ContractAgreement.objects.filter(pk=contract_agreement.pk).exists())
        contract_agreement_pk = contract_agreement.pk
        contract_agreement.delete()
        self.assertFalse(
            ContractAgreement.objects.filter(pk=contract_agreement_pk).exists())


class ContractAgreementQuerySetTests(TestCase):
    @unittest.skip('not implemented yet')
    def test_pending_filter(self):
        raise NotImplementedError


def compare_ownerships(self, save_ownership, find_ownership):
    self.assertEqual(save_ownership.id, find_ownership.id)
    self.assertEqual(save_ownership.datetime, find_ownership.datetime)
    self.assertEqual(save_ownership.prev_owner, find_ownership.prev_owner)
    self.assertEqual(save_ownership.new_owner, find_ownership.new_owner)
    self.assertEqual(save_ownership.btc_tx, find_ownership.btc_tx)
    self.assertEqual(save_ownership.prev_btc_address, find_ownership.prev_btc_address)
    self.assertEqual(save_ownership.new_btc_address, find_ownership.new_btc_address)
    self.assertEqual(save_ownership.type, find_ownership.type)
    self.assertEqual(find_ownership.type, save_ownership.__class__.__name__)
    self.assertEqual(save_ownership.ciphertext_wif, find_ownership.ciphertext_wif)
    self.assertEqual(save_ownership.datetime_response, find_ownership.datetime_response)
    self.assertEqual(save_ownership.datetime_from, find_ownership.datetime_from)
    self.assertEqual(save_ownership.datetime_to, find_ownership.datetime_to)
    self.assertEqual(save_ownership.status, find_ownership.status)
    compare_pieces(self, save_ownership.piece, find_ownership.piece)
    compare_editions(self, save_ownership.edition, find_ownership.edition)


def compare_pieces(self, save_piece, find_piece):
    self.assertEqual(save_piece.id, find_piece.id)
    self.assertEqual(save_piece.title, find_piece.title)
    self.assertEqual(save_piece.artist_name, find_piece.artist_name)
    self.assertEqual(save_piece.date_created, find_piece.date_created)
    self.assertEqual(save_piece.extra_data, find_piece.extra_data)
    self.assertEqual(save_piece.num_editions, find_piece.num_editions)
    self.assertEqual(save_piece.user_registered, find_piece.user_registered)
    self.assertEqual(save_piece.datetime_registered, find_piece.datetime_registered)


def compare_editions(self, save_edition, find_edition):
    self.assertEqual(save_edition.edition_number, find_edition.edition_number)
    self.assertEqual(save_edition.bitcoin_path, find_edition.bitcoin_path)
    self.assertEqual(save_edition.bitcoin_id, find_edition.bitcoin_id)
    self.assertEqual(save_edition.extra_data, find_edition.extra_data)
    self.assertEqual(save_edition.owner, find_edition.owner)


def compare_loan_details(self, save_details, find_details):
    self.assertEqual(save_details.id, find_details.id)
    self.assertEqual(save_details.datetime, find_details.datetime)
    self.assertEqual(save_details.gallery, find_details.gallery)
    self.assertEqual(save_details.contract_model.blob.key,
                     find_details.contract_model.blob.key)
