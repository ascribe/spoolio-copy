# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.datetime_safe import datetime

import boto
import pytest
from boto.s3.key import Key
from moto import mock_s3
from oauth2_provider.models import AccessToken, get_application_model
from pycoin.key.BIP32Node import BIP32Node


pytestmark = pytest.mark.django_db
Application = get_application_model()


@pytest.fixture
def s3_bucket(request):
    mock = mock_s3()
    mock.start()
    s3_connection = boto.connect_s3()
    bucket = s3_connection.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)

    def stop_mock():
        mock.stop()
    request.addfinalizer(stop_mock)
    return bucket


# TODO This is to work around the use of util.util.mainAdminUser
@pytest.fixture
def djroot_user():
    djroot = get_user_model().objects.create(
        email='djangoroot@ascribe.io',
        is_staff=True,
        is_superuser=True,
        username='djroot',
    )
    djroot.set_password('secret-djroot')
    djroot.save()
    return djroot


@pytest.fixture
def alice_password():
    return 'secret-alice'


@pytest.fixture
def alice(request, alice_password):
    username = request.fixturename
    email = '{}@test.com'.format(username)
    alice = get_user_model().objects.create(email=email, username=username)
    alice.set_password(alice_password)
    alice.save()
    return alice


@pytest.fixture
def bob_password():
    return 'secret-bob'


@pytest.fixture
def bob(request, bob_password):
    username = request.fixturename
    email = '{}@test.com'.format(username)
    bob = get_user_model().objects.create(email=email, username=username)
    bob.set_password(bob_password)
    bob.save()
    return bob


@pytest.fixture
def invited_dan_password():
    return 'secret-invited-dan'


@pytest.fixture
def invited_dan(request, invited_dan_password):
    from users.models import UserNeedsToRegisterRole
    username = request.fixturename
    email = '{}@test.com'.format(username)
    invited_dan = get_user_model().objects.create(email=email, username=username)
    invited_dan.set_password(invited_dan_password)
    invited_dan.save()
    # In the system, an invited user, is a user that has
    # a UserNeedsToRegisterRole attached to it
    UserNeedsToRegisterRole.create(user=invited_dan, role=None).save()
    return invited_dan


@pytest.fixture
def invited_erin_password():
    return 'secret-invited-erin'


@pytest.fixture
def invited_erin(request, invited_erin_password):
    from users.models import UserNeedsToRegisterRole
    username = request.fixturename
    email = '{}@test.com'.format(username)
    invited_erin = get_user_model().objects.create(email=email, username=username)
    invited_erin.set_password(invited_erin_password)
    invited_erin.save()
    # In the system, an invited user, is a user that has
    # a UserNeedsToRegisterRole attached to it
    UserNeedsToRegisterRole.create(user=invited_erin, role=None).save()
    return invited_erin


@pytest.fixture
def carol_password():
    return 'secret-carol'


@pytest.fixture
def carol(request, carol_password):
    username = request.fixturename
    email = '{}@test.com'.format(username)
    carol = get_user_model().objects.create(email=email, username=username)
    carol.set_password(carol_password)
    carol.save()
    return carol


@pytest.fixture
def merlin_password():
    return 'secret-merlin'


@pytest.fixture
def merlin(request, merlin_password):
    username = request.fixturename
    email = '{}@test.com'.format(username)
    user = get_user_model().objects.create(email=email, username=username)
    user.set_password(merlin_password)
    user.save()
    return user


@pytest.fixture
def oauth_user(request, oauth_user_password):
    username = request.fixturename
    email = '{}@test.com'.format(username)
    oauth_user = get_user_model().objects.create(email=email, username=username)
    oauth_user.set_password(oauth_user_password)
    oauth_user.save()
    return oauth_user


@pytest.fixture
def oauth_user_password():
    return 'secret-oauth_user'


@pytest.fixture
def oauth_application(request, oauth_user):
    name = request.fixturename + '_fixture'
    return Application.objects.create(name=name, redirect_uris="",
                                      user=oauth_user,
                                      client_type=Application.CLIENT_CONFIDENTIAL,
                                      authorization_grant_type=Application.GRANT_PASSWORD)


@pytest.fixture
def oauth_application_token(oauth_application):
    expires = timezone.now() + timedelta(days=1)
    return AccessToken.objects.create(user=oauth_application.user,
                                      token='1234567890',
                                      application=oauth_application,
                                      expires=expires,
                                      scope='read write')


@pytest.fixture
def license():
    from ownership.models import License
    return License.objects.create(
        code='default',
        name='All rights reserved',
        organization='ascribe',
        url='https://www.ascribe.io/faq/#legals',
    )


@pytest.fixture
def djroot_bitcoin_wallet(djroot_user, monkeypatch):
    from pycoin.key.BIP32Node import BIP32Node
    from bitcoin.models import BitcoinWallet
    netcode = 'XTN' if settings.BTC_TESTNET else 'BTC'
    private_wallet = BIP32Node.from_master_secret('secret-djroot',
                                                  netcode=netcode)
    public_key = private_wallet.wallet_key(as_private=False)
    djroot_wallet = BitcoinWallet.create(djroot_user, public_key=public_key)
    djroot_wallet.save()
    monkeypatch.setattr(
        'django.conf.settings.BTC_MAIN_WALLET', djroot_wallet.address)
    return djroot_wallet


@pytest.fixture
def alice_bitcoin_wallet(alice, alice_password):
    from bitcoin.models import BitcoinWallet
    # TODO remove the try/except clause, and make the creation more explicit,
    # i.e.: via Bitcoin.objects.create() with required parameters
    try:
        alice_wallet = BitcoinWallet.objects.get(user=alice)
    except BitcoinWallet.DoesNotExist:
        alice_wallet = BitcoinWallet.create(alice, password=alice_password)
        alice_wallet.save()
    return alice_wallet


@pytest.fixture
def bob_pubkey(bob, bob_password):
    return BIP32Node.from_master_secret(
        bob_password + bob.email, netcode='XTN').wallet_key(as_private=False)


@pytest.fixture
def bob_bitcoin_wallet(bob, bob_pubkey):
    from bitcoin.models import BitcoinWallet
    return BitcoinWallet.objects.create(user=bob, public_key=bob_pubkey)


@pytest.fixture
def invited_dan_bitcoin_wallet(invited_dan, invited_dan_password):
    from bitcoin.models import BitcoinWallet
    # TODO remove the try/except clause, and make the creation more explicit,
    # i.e.: via Bitcoin.objects.create() with required parameters
    try:
        invited_dan_wallet = BitcoinWallet.objects.get(user=invited_dan)
    except BitcoinWallet.DoesNotExist:
        invited_dan_wallet = BitcoinWallet.create(invited_dan, password=invited_dan_password)
        invited_dan_wallet.save()
    return invited_dan_wallet


@pytest.fixture
def invited_erin_bitcoin_wallet(invited_erin, invited_erin_password):
    from bitcoin.models import BitcoinWallet
    # TODO remove the try/except clause, and make the creation more explicit,
    # i.e.: via Bitcoin.objects.create() with required parameters
    try:
        invited_erin_wallet = BitcoinWallet.objects.get(user=invited_erin)
    except BitcoinWallet.DoesNotExist:
        invited_erin_wallet = BitcoinWallet.create(invited_erin, password=invited_erin_password)
        invited_erin_wallet.save()
    return invited_erin_wallet


@pytest.fixture
def digital_work_alice(alice, s3_bucket):
    from blobs.models import DigitalWork, File
    key = File.create_key('digitalwork', 'alice_work.gif', user=alice)
    k = Key(s3_bucket)
    k.key = key
    k.set_contents_from_string('abc')
    digital_work = DigitalWork.objects.create(
        user=alice,
        digital_work_file=key,
    )
    return digital_work


@pytest.fixture
def thumbnail_alice(alice):
    from blobs.models import Thumbnail
    return Thumbnail.objects.create(user=alice,
                                    thumbnail_file=settings.THUMBNAIL_DEFAULT)


@pytest.fixture
def piece_alice(djroot_bitcoin_wallet, alice_bitcoin_wallet,
                digital_work_alice, thumbnail_alice):
    from piece.models import Piece
    alice = alice_bitcoin_wallet.user
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    return Piece.objects.create(
        user_registered=alice,
        date_created=timezone.now().date(),
        digital_work=digital_work_alice,
        thumbnail=thumbnail_alice,
        title='wonderalice',
        bitcoin_path=bitcoin_path,
    )


@pytest.fixture
def edition_alice(djroot_bitcoin_wallet, piece_alice, alice_bitcoin_wallet):
    from piece.models import Edition
    alice = alice_bitcoin_wallet.user
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    edition = Edition.objects.create(
        parent=piece_alice,
        bitcoin_path=bitcoin_path,
        edition_number=1,
        owner=alice,
    )
    piece_alice.num_editions = 1
    piece_alice.save()
    return edition


@pytest.fixture
def ownership_piece_alice(request, piece_alice):
    from ownership.models import OwnershipPiece
    from django.db.models import signals
    from bitcoin.signals import on_ownership_piece_create
    signals.post_save.disconnect(
        receiver=on_ownership_piece_create,
        sender=OwnershipPiece,
        #dispatch_uid='bitcoin_on_ownership_piece_create',
    )

    def fin():
        signals.post_save.connect(
            on_ownership_piece_create,
            sender=OwnershipPiece,
            #dispatch_uid='bitcoin_on_ownership_piece_create',
        )
    request.addfinalizer(fin)
    alice = piece_alice.user_registered
    return OwnershipPiece.objects.create(
        piece=piece_alice, new_owner=alice, prev_owner=alice)


@pytest.fixture
def ownership_edition_alice(request, edition_alice):
    from ownership.models import OwnershipEditions
    from django.db.models import signals
    from bitcoin.signals import on_ownership_editions_create
    signals.post_save.disconnect(
        receiver=on_ownership_editions_create,
        sender=OwnershipEditions,
        #dispatch_uid='bitcoin_on_ownership_editions_create',
    )

    def fin():
        signals.post_save.connect(
            on_ownership_editions_create,
            sender=OwnershipEditions,
            #dispatch_uid='bitcoin_on_ownership_editions_create',
        )
    request.addfinalizer(fin)
    alice = edition_alice.user_registered
    return OwnershipEditions.objects.create(
        piece=edition_alice.parent, new_owner=alice, prev_owner=alice)


@pytest.fixture
def loan_edition(request, edition_alice, bob_bitcoin_wallet):
    from ownership.models import Loan
    return Loan.objects.create(
        piece=edition_alice.parent,
        edition=edition_alice,
        new_owner=bob_bitcoin_wallet.user,
        prev_owner=edition_alice.user_registered,
        datetime_from=timezone.now(),
        datetime_to=timezone.now(),
        type='Loan',
    )


@pytest.fixture
def loan_piece(request, piece_alice, bob_bitcoin_wallet):
    from ownership.models import LoanPiece
    return LoanPiece.objects.create(
        piece=piece_alice,
        new_owner=bob_bitcoin_wallet.user,
        prev_owner=piece_alice.user_registered,
        datetime_from=timezone.now(),
        datetime_to=timezone.now(),
        type=LoanPiece.__name__,
    )


@pytest.fixture
def ownership(request, edition_alice, bob):
    from ownership.models import Ownership
    return Ownership.objects.create(
        edition=edition_alice,
        new_owner=bob,
        prev_owner=edition_alice.user_registered,
        piece=edition_alice.parent,
        type='Ownership',
    )


@pytest.fixture
def ownership_transfer(request, registered_edition_alice, alice, bob):
    from ownership.models import OwnershipTransfer
    from django.db.models import signals
    from acl.signals import on_ownership_transfer_create
    signals.post_save.disconnect(
        receiver=on_ownership_transfer_create,
        sender=OwnershipTransfer,
    )

    def fin():
        signals.post_save.connect(
            on_ownership_transfer_create,
            sender=OwnershipTransfer,
        )
    request.addfinalizer(fin)
    return OwnershipTransfer.objects.create(
        edition=registered_edition_alice,
        new_owner=bob,
        prev_owner=alice,
        piece=registered_edition_alice.parent,
        type='OwnershipTransfer'
    )


@pytest.fixture
def registered_piece_alice(djroot_bitcoin_wallet, alice_bitcoin_wallet,
                           digital_work_alice, thumbnail_alice):
    from ownership.models import OwnershipPiece
    from piece.models import Piece
    alice = alice_bitcoin_wallet.user
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    # TODO Remove created logic if not needed -- keeping it for now just in
    # case -- the fixture mechanisms are expected to be such that an object
    # gets created only once.
    piece, created = Piece.objects.get_or_create(
        user_registered=alice,
        date_created=timezone.now().date(),
        digital_work=digital_work_alice,
        thumbnail=thumbnail_alice,
        title='wonderalice',
        bitcoin_path=bitcoin_path,
    )
    if created:
        OwnershipPiece.objects.create(
            piece=piece, new_owner=alice, prev_owner=alice)
    return piece


@pytest.fixture
def registered_edition_alice(djroot_bitcoin_wallet, registered_piece_alice, alice_bitcoin_wallet):
    from acl.models import ActionControl
    from ownership.models import OwnershipEditions
    from piece.models import Edition
    alice = alice_bitcoin_wallet.user
    bitcoin_path = alice_bitcoin_wallet.create_new_address()
    edition = Edition.objects.create(
        parent=registered_piece_alice,
        bitcoin_path=bitcoin_path,
        edition_number=1,
        owner=alice,
    )
    registered_piece_alice.num_editions = 1
    registered_piece_alice.save()
    ownership_editions = OwnershipEditions.create(
        edition=registered_piece_alice,
        new_owner=alice,
    )
    ownership_editions.save()
    ActionControl.set_acl_registree_edition(user=alice, edition=edition)
    return edition


@pytest.fixture
def piece(alice, digital_work):
    from piece.models import Piece
    return Piece.objects.create(
        user_registered=alice,
        date_created=datetime.today().date(),
        digital_work=digital_work,
    )


@pytest.fixture
def piece_with_thumbnail(alice, digital_work, thumbnail):
    from piece.models import Piece
    return Piece.objects.create(
        user_registered=alice,
        date_created=datetime.today().date(),
        digital_work=digital_work,
        thumbnail=thumbnail,
    )


@pytest.fixture
def edition(piece):
    from piece.models import Edition
    alice = piece.user_registered
    edition = Edition.objects.create(
        parent=piece,
        edition_number=1,
        owner=alice,
    )
    # TODO this should be coded into Piece.save()
    piece.num_editions = 1
    piece.save()
    return edition


@pytest.fixture
def digital_work(alice, s3_bucket):
    from blobs.models import DigitalWork, File
    key = File.create_key('digitalwork', 'alice_work.gif', user=alice)
    k = Key(s3_bucket)
    k.key = key
    k.set_contents_from_string('abc')
    return DigitalWork.objects.create(user=alice, digital_work_file=key)


@pytest.fixture
def thumbnail(alice):
    from blobs.models import Thumbnail
    return Thumbnail.objects.create(user=alice,
                                    thumbnail_file=settings.THUMBNAIL_DEFAULT)


@pytest.fixture
def whitelabel(merlin):
    from whitelabel.models import WhitelabelSettings
    return WhitelabelSettings.objects.create(
        user=merlin,
        subdomain='subdomain',
        name='subdomain',
        title='subdomain',
        logo='logo',
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
