from django.db.utils import DataError
from django.test import TestCase
from django.utils.datetime_safe import datetime
from django.utils import timezone

import pytz
import pytest

from django.conf import settings
from blobs.models import DigitalWork
from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from piece.models import Piece
from users.test.util import APIUtilUsers

__author__ = 'dimi'

FIX_URL_JPG = 'http://ascribe0.s3.amazonaws.com/media/thumbnails/ascribe_spiral.png'
FIX_KEY_PNG = 'ascribe_spiral.png'

pytestmark = pytest.mark.django_db


class PieceTestCase(TestCase, APIUtilUsers, APIUtilDigitalWork, APIUtilThumbnail):
    def setUp(self):
        self.password = '0' * 10
        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    def testCreatePiece(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=datetime.today().date(),
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           thumbnail=self.thumbnail_user1,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(title='title')
        # Comparing model instances for equality
        # https://docs.djangoproject.com/en/dev/topics/db/queries/#comparing-objects
        self.assertTrue(save_piece == find_piece)

    def testCreatePieceS3(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           thumbnail=self.thumbnail_user1,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(title='title')
        self.assertTrue(save_piece == find_piece)

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)

        self.assertNotEqual(save_piece.thumbnail, None)
        self.assertNotEqual(save_piece.digital_work, None)
        self.assertNotEqual(save_piece.other_data, None)

    def testCreatePieceNoThumb(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(title='title')
        self.assertTrue(save_piece == find_piece)

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)

    def testCreatePieceTitle(self):
        user = self.user1

        long_title = 'a'*180
        save_piece = Piece(title=long_title,
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)

        extra_long_title = 'a'*1000
        save_piece = Piece(title=extra_long_title,
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)

        with self.assertRaises(DataError):
            save_piece.save()

    def testCreatePieceDate(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)
        self.assertEqual(find_piece.date_created, self.date)
        self.assertGreater(datetime.today().replace(tzinfo=pytz.UTC), find_piece.datetime_registered)

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertEqual(find_piece.datetime_registered.date(), datetime.utcnow().replace(tzinfo=timezone.utc).date())

    def testCreatePieceExtraData(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=datetime.today().date(),
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)

        self.assertNotEqual(save_piece.digital_work, None)
        self.assertEqual(len(find_piece.extra_data), 1)

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=datetime.today().date(),
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()
        find_piece = Piece.objects.get(id=save_piece.id)
        self.assertTrue(save_piece == find_piece)
        self.assertEqual(find_piece.extra_data, {})

    def testUpdatePiece(self):
        user = self.user1

        save_piece = Piece(title='title',
                           artist_name='artist_name',
                           date_created=self.date,
                           extra_data={'extra_data_string': 'something'},
                           num_editions=2,
                           user_registered=user,
                           digital_work=self.digitalwork_user1)
        save_piece.save()

        old_id = save_piece.id

        digital_work_2 = DigitalWork(user=user, key=FIX_KEY_PNG,
                                     digital_work_hash='hash2')
        digital_work_2.save()

        save_piece.digital_work = digital_work_2
        save_piece.title = 'updated_title'

        save_piece.save()

        find_piece = Piece.objects.get(title='updated_title')
        self.assertTrue(save_piece == find_piece)
        self.assertEqual(old_id, find_piece.id)


@pytest.mark.usefixtures('license',
                         'djroot_bitcoin_wallet',
                         'alice_bitcoin_wallet')
def test_register_editions(registered_piece_alice):
    from bitcoin.bitcoin_service import BitcoinService
    from bitcoin.models import BitcoinTransaction, BitcoinWallet, TX_PENDING
    from ownership.models import OwnershipEditions
    from acl.models import ActionControl
    from ..models import Edition
    from ..tasks import register_editions

    # Test can be used with any number of editions.
    # We use 1 for speed reasons.
    num_editions = 1
    alice = registered_piece_alice.user_registered
    piece_alice = registered_piece_alice

    editions_tasks = register_editions(piece_alice,
                                       alice,
                                       num_editions).delay()
    assert editions_tasks.failed() is False

    # We test if the editions returned
    # were correctly inserted into the database
    editions = editions_tasks.get()

    assert all(
        Edition.objects.filter(parent=piece_alice,
                               bitcoin_path__icontains=e.bitcoin_id).exists()
        for e in editions)
    assert piece_alice.num_editions == num_editions
    assert len(editions) == num_editions

    # We test if the ACLs for the respective user
    # and their editions have been set appropriately
    acls = ActionControl.objects.filter(
        user=alice, piece=piece_alice, edition__in=editions)
    for acl in acls:
        assert acl.acl_view is True
        assert acl.acl_edit is True
        assert acl.acl_download is True
        assert acl.acl_delete is True
        assert acl.acl_create_editions is False
        assert acl.acl_share is True
        assert acl.acl_unshare is False
        assert acl.acl_transfer is True
        assert acl.acl_withdraw_transfer is False
        assert acl.acl_consign is True
        assert acl.acl_withdraw_consign is False
        assert acl.acl_unconsign is False
        assert acl.acl_request_unconsign is False
        assert acl.acl_loan is True
        assert acl.acl_coa is True

    # We test if an OwnershipEditions object and
    # a related BitcoinTransaction were created
    editions_ownership = OwnershipEditions.objects.get(piece=piece_alice,
                                                       new_owner=alice)
    assert editions_ownership.piece == piece_alice

    btc_tx = BitcoinTransaction.objects.get(pk=editions_ownership.btc_tx.id)
    assert btc_tx.from_address == BitcoinWallet.mainAdminBtcAddress()
    assert btc_tx.outputs == [
        (BitcoinService.minDustSize, piece_alice.hash_as_address_no_metada()),
        (BitcoinService.minDustSize, piece_alice.hash_as_address()),
        (BitcoinService.minDustSize, piece_alice.bitcoin_id)
    ]
    assert btc_tx.spoolverb == 'ASCRIBESPOOL01EDITIONS{}'.format(num_editions)
    assert btc_tx.status == TX_PENDING


@pytest.mark.usefixtures('djroot_user')
def test_empty_ownership_history(registered_edition_alice):
    ownership_history = registered_edition_alice.ownership_history
    assert len(ownership_history) == 1
    assert (ownership_history[0][1] ==
            'Registered by {}'.format(registered_edition_alice.owner))


# TODO move to ownership app
@pytest.mark.usefixtures('djroot_user')
def test_pending_state_in_ownership_history(alice,
                                            alice_password,
                                            registered_edition_alice,
                                            bob_bitcoin_wallet,
                                            bob_password,
                                            invited_dan_bitcoin_wallet):
    from ..models import OwnershipTransfer
    from bitcoin.models import BitcoinWallet
    from ownership.api import TransferEndpoint
    from ownership.signals import transfer_created

    # first transfer to non-invited user
    bob = bob_bitcoin_wallet.user
    first_transfer = OwnershipTransfer.create(
        edition=registered_edition_alice,
        prev_owner=alice,
        transferee=bob,
        prev_btc_address=None,
    )
    first_transfer.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(first_transfer, alice_password)
    first_transfer.save()
    transfer_created.send(sender=TransferEndpoint, instance=first_transfer, password=alice_password)
    registered_edition_alice.owner= bob
    registered_edition_alice.save()

    # second, transfer ownership to invited user
    invited_dan = invited_dan_bitcoin_wallet.user
    second_transfer = OwnershipTransfer.create(
        edition=registered_edition_alice,
        prev_owner=bob,
        transferee=invited_dan,
        prev_btc_address=None,
    )
    second_transfer.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(second_transfer, bob_password)
    second_transfer.save()

    transfer_created.send(sender=TransferEndpoint, instance=second_transfer, password=bob_password)
    registered_edition_alice.pending_new_owner = invited_dan
    registered_edition_alice.save()

    _, transfer_bob_str, transfer_invited_dan_str = [s[1] for s in registered_edition_alice.ownership_history]

    assert '(pending)' not in transfer_bob_str
    assert '(pending)' in transfer_invited_dan_str
