from functools import wraps
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.datetime_safe import datetime

import boto

from moto import mock_s3


class DynamicFixtureError(Exception):
    pass


def _s3_bucket():
    s3_connection = boto.connect_s3()
    return s3_connection.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)


def mock_s3_bucket(test_function):
    @wraps(test_function)
    @mock_s3
    def wrapper(*args, **kwargs):
        _s3_bucket()
        return test_function(*args, **kwargs)
    return wrapper


# TODO This is to work around the use of util.util.mainAdminUser
def _djroot_user():
    djroot, created = User.objects.get_or_create(
        email='djangoroot@ascribe.io',
        is_staff=True,
        is_superuser=True,
        username='djroot',
    )
    if created:
        djroot.set_password('secret-djroot')
        djroot.save()
    return djroot


def _alice():
    alice, created = User.objects.get_or_create(email='alice@test.com',
                                                username='alice')
    if created:
        alice.set_password('secret-alice')
        alice.save()
    return alice


def _bob():
    bob, created = User.objects.get_or_create(
        email='bob@test.com',
        username='bob',
    )
    if created:
        bob.set_password('secret-bob')
        bob.save()
    return bob


def _merlin():
    merlin, created = User.objects.get_or_create(email='merlin@test.com',
                                                 username='merlin')
    if created:
        merlin.set_password('secret-merlin')
        merlin.save()
    return merlin


def _prize_admin():
    return User.objects.get_or_create(username='prize_admin',
                                      email='admin@pri.ze')[0]


def _juror():
    return User.objects.get_or_create(username='juror',
                                      email='juror@ju.ry')[0]


def _juror_jane():
    return User.objects.get_or_create(username='juror_jane',
                                      email='jane@ju.ry')[0]


def _juror_joe():
    return User.objects.get_or_create(username='juror_joe',
                                      email='joe@ju.ry')[0]


def _judge():
    return User.objects.get_or_create(username='judge',
                                      email='judge@fud.ge.')[0]


def _license():
    from ownership.models import License
    license, _ = License.objects.get_or_create(code='license-to-create')
    return license


def _digital_work():
    from blobs.models import DigitalWork
    return DigitalWork.objects.create()


def _digital_work_alice():
    from blobs.models import DigitalWork
    alice = _alice()
    digital_work, _ = DigitalWork.objects.get_or_create(
        user=alice,
        digital_work_file='dummmy.txt',
        digital_work_hash='dummyhash',
    )
    return digital_work


def _digital_work_bob():
    from blobs.models import DigitalWork
    digital_work, _ = DigitalWork.objects.get_or_create(user=_bob())
    return digital_work


def _s3_mocked_digital_work_alice():
    from blobs.models import DigitalWork
    from util.util import hash_string
    alice = _alice()
    uuid = uuid4()
    alice_hash = hash_string(str(alice.pk))
    digital_work_file = 'local/{}/{}/digitalwork/{}.gif'.format(
        alice_hash,
        uuid,
        uuid,
    )
    digital_work, _ = DigitalWork.objects.get_or_create(
        user=alice,
        digital_work_file=digital_work_file,
    )
    return digital_work


def _piece():
    from piece.models import Piece
    alice = _alice()
    digital_work = _digital_work()
    return Piece.objects.get_or_create(
        user_registered=alice,
        date_created=datetime.today().date(),
        digital_work=digital_work,
    )[0]


def _piece_alice():
    from piece.models import Piece
    alice = _alice()
    digital_work = _digital_work_alice()
    return Piece.objects.get_or_create(
        user_registered=alice,
        date_created=datetime.today().date(),
        digital_work=digital_work,
        title='wonderalice',
    )[0]


def _piece_bob():
    from piece.models import Piece
    bob = _bob()
    digital_work = _digital_work_bob()
    return Piece.objects.get_or_create(
        user_registered=bob,
        date_created=datetime.today().date(),
        digital_work=digital_work,
        title='wonderbob',
    )[0]


def _edition_alice():
    from piece.models import Edition
    alice = _alice()
    piece = _piece_alice()
    return Edition.objects.create(owner=alice, edition_number=1, parent=piece)


def _registered_piece_alice():
    from blobs.models import Thumbnail
    from ownership.models import OwnershipPiece
    from piece.models import Piece
    _djroot_bitcoin_wallet()
    alice_bitcoin_wallet = _alice_bitcoin_wallet()
    alice = alice_bitcoin_wallet.user
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    digital_work = _s3_mocked_digital_work_alice()
    thumbnail = Thumbnail.objects.create(
        user=alice, thumbnail_file=settings.THUMBNAIL_DEFAULT)
    piece, created = Piece.objects.get_or_create(
        user_registered=alice,
        date_created=datetime.today().date(),
        digital_work=digital_work,
        thumbnail=thumbnail,
        title='wonderalice',
        bitcoin_path=bitcoin_path,
    )
    if created:
        OwnershipPiece.objects.create(
            piece=piece, new_owner=alice, prev_owner=alice)
    return piece


def _registered_edition_alice():
    from acl.models import ActionControl
    from ownership.models import OwnershipEditions
    from piece.models import Edition
    piece = _registered_piece_alice()
    alice_bitcoin_wallet = _alice_bitcoin_wallet()
    alice = piece.user_registered
    if piece.num_editions != -1:
        raise DynamicFixtureError(
            'Expecting piece.num_editions to be "-1", not "{}"'.format(
                piece.num_editions)
        )

    # piece.num_editions = 0
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    edition = Edition.objects.create(
        parent=piece,
        bitcoin_path=bitcoin_path,
        edition_number=1,
        owner=alice,
    )
    piece.num_editions = 1
    piece.save()
    ownership_editions = OwnershipEditions.create(
        edition=piece,
        new_owner=alice,
    )
    ownership_editions.save()
    ActionControl.set_acl_registree_edition(user=alice, edition=edition)
    return edition


def _registered_edition_pair_alice():
    """
    Set of two registered editions.

    """
    from acl.models import ActionControl
    from ownership.models import OwnershipEditions
    from piece.models import Edition
    piece = _registered_piece_alice()
    alice_bitcoin_wallet = _alice_bitcoin_wallet()
    alice = piece.user_registered
    if piece.num_editions != -1:
        raise DynamicFixtureError(
            'Expecting piece.num_editions to be "-1", not "{}"'.format(
                piece.num_editions)
        )
    # first edition
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    edition_one = Edition.objects.create(
        parent=piece,
        bitcoin_path=bitcoin_path,
        edition_number=1,
        owner=alice,
    )
    piece.num_editions = 1
    piece.save()
    ownership_editions = OwnershipEditions.create(
        edition=piece,
        new_owner=alice,
    )
    ownership_editions.save()
    ActionControl.set_acl_registree_edition(user=alice, edition=edition_one)

    # second edition
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    edition_two = Edition.objects.create(
        parent=piece,
        bitcoin_path=bitcoin_path,
        edition_number=2,
        owner=alice,
    )
    piece.num_editions = 2
    piece.save()
    ownership_editions = OwnershipEditions.create(
        edition=piece,
        new_owner=alice,
    )
    ownership_editions.save()
    ActionControl.set_acl_registree_edition(user=alice, edition=edition_two)
    return edition_one, edition_two


def _whitelabel_merlin(subdomain='subdomain',
                       name='subdomain',
                       title='subdomain',
                       logo='logo'):
    from whitelabel.models import WhitelabelSettings
    merlin = _merlin()
    whitelabel, _ = WhitelabelSettings.objects.get_or_create(
        user=merlin,
        subdomain=subdomain,
        name=name,
        title=title,
        logo=logo,
        acl_create_editions=True,
        acl_wallet_submitted=True,
        acl_coa=True,
        acl_share=True,
        acl_edit_public_contract=True,
        acl_transfer=True,
        acl_view_settings_api=False,
        acl_view=True,
        acl_withdraw_transfer=True,
        acl_unconsign=True,
        acl_request_unconsign=True,
        acl_download=True,
        acl_withdraw_consign=True,
        acl_view_powered_by=True,
        acl_wallet_accepted=True,
        acl_wallet_submit=True,
        acl_consign=True,
        acl_view_settings_bitcoin=False,
        acl_view_settings_account_hash=False,
        acl_edit=True,
    )
    return whitelabel


def _whitelabel_settings(subdomain='whitelabel'):
    from whitelabel.models import WhitelabelSettings
    return WhitelabelSettings.objects.get_or_create(
        user=_alice(),
        subdomain=subdomain,
        name=subdomain,
    )[0]


def _prize_with_whitelabel(subdomain='whitelabel'):
    from prize.models import Prize
    whitelabel_settings = _whitelabel_settings(subdomain=subdomain)
    prize, _ = Prize.objects.get_or_create(
        whitelabel_settings=whitelabel_settings,
        active=True,
        num_submissions=1,
    )
    return prize


def _prize_juror(subdomain='whitelabel'):
    from prize.models import PrizeUser
    return PrizeUser.objects.get_or_create(
        user=_juror(),
        prize=_prize_with_whitelabel(subdomain=subdomain),
        is_jury=True,
    )[0]


def _prize_juror_jane(subdomain='whitelabel'):
    from prize.models import PrizeUser
    return PrizeUser.objects.get_or_create(
        user=_juror_jane(),
        prize=_prize_with_whitelabel(subdomain=subdomain),
        is_jury=True,
    )[0]


def _prize_juror_joe(subdomain='whitelabel'):
    from prize.models import PrizeUser
    return PrizeUser.objects.get_or_create(
        user=_juror_joe(),
        prize=_prize_with_whitelabel(subdomain=subdomain),
        is_jury=True,
    )[0]


def _prize_judge(subdomain='whitelabel'):
    from prize.models import PrizeUser
    return PrizeUser.objects.get_or_create(
        user=_judge(),
        prize=_prize_with_whitelabel(subdomain=subdomain),
        is_judge=True,
    )[0]


def _prize_piece_alice(subdomain='whitelabel'):
    from prize.models import PrizePiece
    piece = _piece_alice()
    prize = _prize_with_whitelabel(subdomain=subdomain)
    user = piece.user_registered
    return PrizePiece.objects.create(piece=piece, prize=prize, user=user)


def _prize_piece_bob(subdomain='whitelabel'):
    from prize.models import PrizePiece
    piece = _piece_bob()
    prize = _prize_with_whitelabel(subdomain=subdomain)
    user = piece.user_registered
    return PrizePiece.objects.create(piece=piece, prize=prize, user=user)


def _rating_piece_alice(subdomain='whitelabel'):
    from prize.models import Rating
    user = _prize_juror(subdomain=subdomain).user
    piece = _piece_alice()
    return Rating.objects.get_or_create(
        user=user,
        piece=piece,
        note='9',
        type=Rating.__name__,
    )[0]


def _rating_piece_bob(subdomain='whitelabel'):
    from prize.models import Rating
    user = _prize_juror(subdomain=subdomain).user
    piece = _piece_bob()
    return Rating.objects.get_or_create(
        user=user,
        piece=piece,
        note='7',
        type=Rating.__name__,
    )[0]


def _rating_one_piece_alice(subdomain='whitelabel'):
    from prize.models import Rating
    user = _prize_juror(subdomain=subdomain).user
    piece = _piece_alice()
    return Rating.objects.get_or_create(
        user=user,
        piece=piece,
        note='3',
        type=Rating.__name__,
    )[0]


def _rating_two_piece_alice(subdomain='whitelabel'):
    from prize.models import Rating
    user = _prize_juror(subdomain=subdomain).user
    piece = _piece_alice()
    return Rating.objects.get_or_create(
        user=user,
        piece=piece,
        note='5',
        type=Rating.__name__,
    )[0]


def _rating_three_piece_alice(subdomain='whitelabel'):
    from prize.models import Rating
    user = _prize_juror(subdomain=subdomain).user
    piece = _piece_alice()
    return Rating.objects.get_or_create(
        user=user,
        piece=piece,
        note='7',
        type=Rating.__name__,
    )[0]


def _djroot_bitcoin_wallet():
    from pycoin.key.BIP32Node import BIP32Node
    from bitcoin.models import BitcoinWallet
    djroot = _djroot_user()
    netcode = 'XTN' if settings.BTC_TESTNET else 'BTC'
    private_wallet = BIP32Node.from_master_secret('secret-djroot',
                                                  netcode=netcode)
    public_key = private_wallet.wallet_key(as_private=False)
    djroot_wallet = BitcoinWallet.create(djroot, public_key=public_key)
    djroot_wallet.save()
    return djroot_wallet


def _alice_bitcoin_wallet():
    from bitcoin.models import BitcoinWallet
    alice = _alice()
    try:
        alice_wallet = BitcoinWallet.objects.get(user=alice)
    except BitcoinWallet.DoesNotExist:
        alice_wallet = BitcoinWallet.create(alice, password='secret-alice')
        alice_wallet.save()
    return alice_wallet


def _bob_bitcoin_wallet():
    from bitcoin.models import BitcoinWallet
    bob = _bob()
    bob_wallet = BitcoinWallet.create(bob, password='secret-bob')
    bob_wallet.save()
    return bob_wallet
