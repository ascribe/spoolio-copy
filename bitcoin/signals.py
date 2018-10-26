import logging

from pycoin.key.BIP32Node import BIP32Node

from django.apps import apps
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.conf import settings
from acl.models import ActionControl

from ownership import models as ownership_models
from ownership.signals import consignment_confirmed, unconsignment_create, loan_edition_confirm, loan_piece_confirm
from ownership.signals import transfer_created, consignment_created, loan_edition_created, loan_piece_created
from ownership.api import ConsignEndpoint, UnConsignEndpoint, LoanEndpoint, LoanPiece, TransferEndpoint
from ownership.api import LoanPieceEndpoint
from users.api import UserEndpoint
from users.signals import check_pending_actions
from users.models import UserResetPasswordRole
from bitcoin.models import BitcoinTransaction, BitcoinWallet
from bitcoin import tasks

from util import util

logger = logging.getLogger(__name__)


def check_migration(instance):
    # Check to see if an edition needs to be migrated
    role = UserResetPasswordRole.objects.filter(user=instance.prev_owner).order_by('-datetime')
    role = role[0] if role else None

    # if user reset its password
    if role:
        # set the prev_btc_address
        if instance.prev_btc_address:
            prev_btc_address = instance.prev_btc_address
        else:
            prev_btc_address = instance.edition.btc_owner_address

        # get registration
        previous_ownership = ownership_models.Ownership.objects.filter(new_owner=instance.prev_owner,
                                                                       new_btc_address=prev_btc_address
                                                                       ).order_by("-datetime")

        # There is always at least a registration
        previous_ownership = previous_ownership[0]

        # if the previous ownership action was done before the change of password
        # or the previous ownership is a registration
        if role.datetime >= previous_ownership.datetime or previous_ownership.type == 'OwnershipRegistration':
            new_btc_address = BitcoinWallet.walletForUser(instance.prev_owner).create_new_address()
            BitcoinWallet.import_address(new_btc_address, instance.prev_owner).delay()
            if instance.edition:
                migration = ownership_models.OwnershipMigration.create(edition=instance.edition,
                                                                       new_owner=instance.prev_owner)
            else:
                migration = ownership_models.OwnershipMigration.create(edition=None,
                                                                       piece=instance.piece,
                                                                       new_owner=instance.piece.user_registered)
            migration.new_btc_address = new_btc_address
            migration.prev_btc_address = prev_btc_address
            migration.save()
            return migration

    return None


# TODO use dispatch_uid='bitcoin_on_ownership_piece_create' -- see
# https://docs.djangoproject.com/en/1.9/topics/signals/#preventing-duplicate-signals
@receiver(post_save, sender=ownership_models.OwnershipPiece)
def on_ownership_piece_create(sender, instance, created, *args, **kwargs):
    if created:
        # Create bitcoin transaction
        transaction = BitcoinTransaction.register_piece(instance)

        # register piece
        tasks.register_piece.delay(transaction.id, util.mainAdminPassword())


# TODO use dispatch_uid='bitcoin_on_ownership_editions_create' -- see
# https://docs.djangoproject.com/en/1.9/topics/signals/#preventing-duplicate-signals
@receiver(post_save, sender=ownership_models.OwnershipEditions)
def on_ownership_editions_create(sender, instance, created, *args, **kwargs):
    if created:
        # Create bitcoin transaction
        transaction = BitcoinTransaction.editions(instance)

        # register number of editions
        tasks.editions.delay(transaction.id, util.mainAdminPassword())


@receiver(post_save, sender=ownership_models.OwnershipRegistration)
def on_ownership_registration_create(sender, instance, created, *args, **kwargs):
    if created:
        # Create bitcoin transaction
        transaction = BitcoinTransaction.register(instance)

        # register the edition
        tasks.register.delay(transaction.id, util.mainAdminPassword())


@receiver(transfer_created, sender=TransferEndpoint)
def on_ownership_transfer_create(sender, instance, password, *args, **kwargs):
    # Create bitcoin transfer transaction
    transfer = BitcoinTransaction.transfer(instance)

    # if a user needs to register and there is no wallet yet no transaction will be created
    if transfer:

        # before pushing the transaction we need to check:
        # 1. the edition is already registered (because of lazy editions)
        # 2. check if an edition needs migration (due to a password change)
        # 3. the edition address is refilled

        # check if edition is registered
        registration = ownership_models.OwnershipRegistration.objects.filter(edition=instance.edition)
        if not registration:
            registration = ownership_models.OwnershipRegistration.create(edition=instance.edition,
                                                                         new_owner=instance.edition.owner)
            registration.save()

        # check if edition needs migration
        migration = check_migration(instance)
        if migration:
            instance.prev_btc_address = migration.new_btc_address
            instance.btc_tx = None
            instance.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(instance, password)
            instance.save()

            # delete old btc_tx which has the wrong addresses and create a new one
            transfer.delete()
            transfer = BitcoinTransaction.transfer(instance)

        # refill the edition address
        # create the transaction
        refill = BitcoinTransaction.refill(instance)
        # set the transfer as the dependent transaction so that it is sent after the refill by the
        # transaction_monitor
        refill.dependent_tx = transfer
        refill.save()
        tasks.refill.delay(refill.id, util.mainAdminPassword())


@receiver(consignment_created, sender=ConsignEndpoint)
def on_consignment_create(sender, instance, password, *args, **kwargs):
    # upon consignment created we need to check if:
    # 1. An edition is registered
    # 2. If it requires a migration

    # check if edition is registered
    registration = ownership_models.OwnershipRegistration.objects.filter(edition=instance.edition)
    if not registration:
        registration = ownership_models.OwnershipRegistration.create(edition=instance.edition,
                                                                     new_owner=instance.edition.owner)
        registration.save()

    # check migration
    migration = check_migration(instance)
    if migration:
        instance.prev_btc_address = migration.new_btc_address
        instance.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(instance, password)
        instance.save()


@receiver(consignment_confirmed, sender=ConsignEndpoint)
def on_consignment_confirmed(sender, instance, *args, **kwargs):
    # Create bitcoin consign transaction
    consign = BitcoinTransaction.consign(instance)

    # before pushing the transaction we need to check:
    # 1. the edition is already registered (because of lazy editions)
    # 2. the edition address is refilled

    # check if edition is registered
    registration = ownership_models.OwnershipRegistration.objects.filter(edition=instance.edition)
    if not registration:
        registration = ownership_models.OwnershipRegistration.create(edition=instance.edition,
                                                                     new_owner=instance.edition.owner)
        registration.save()

    # refill the edition address
    # create the transaction
    refill = BitcoinTransaction.refill(instance)
    # set the consign as the dependent transaction so that it is sent after the refill by the
    # transaction_monitor
    refill.dependent_tx = consign
    refill.save()
    tasks.refill.delay(refill.id, util.mainAdminPassword())


@receiver(unconsignment_create, sender=UnConsignEndpoint)
def on_unconsignment_create(sender, instance, password, *args, **kwargs):
    # Create bitcoin unconsign transaction
    unconsign = BitcoinTransaction.unconsign(instance)

    # before pushing the transaction we need to check:
    # 1. check if the edition needs migration
    # 2. the edition address is refilled

    # check if edition needs migration
    migration = check_migration(instance)
    if migration:
        instance.prev_btc_address = migration.new_btc_address
        instance.btc_tx = None
        instance.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(instance, password)
        instance.save()

        # delete old btc_tx which has the wrong addresses and create a new one
        unconsign.delete()
        unconsign = BitcoinTransaction.unconsign(instance)

    # refill the edition address
    # create the transaction
    refill = BitcoinTransaction.refill(instance)
    # set the unconsign as the dependent transaction so that it is sent after the refill by the
    # transaction_monitor
    refill.dependent_tx = unconsign
    refill.save()
    tasks.refill.delay(refill.id, util.mainAdminPassword())


@receiver(loan_edition_created, sender=LoanEndpoint)
def on_loan_edition_create(sender, instance, password, *args, **kwargs):
    # upon loan created we need to check if:
    # 1. An edition is registered
    # 2. If it requires a migration

    # check if edition is registered
    registration = ownership_models.OwnershipRegistration.objects.filter(edition=instance.edition)
    if not registration:
        registration = ownership_models.OwnershipRegistration.create(edition=instance.edition,
                                                                     new_owner=instance.edition.owner)
        registration.save()

    # check migration
    migration = check_migration(instance)
    if migration:
        instance.prev_btc_address = migration.new_btc_address
        instance.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(instance, password)
        instance.save()


@receiver(loan_edition_confirm, sender=LoanEndpoint)
def on_loan_edition_confirmed(sender, instance, *args, **kwargs):
    # Create bitcoin consign transaction
    loan = BitcoinTransaction.loan(instance)

    # before pushing the transaction we need to check:
    # 1. the edition is already registered (because of lazy editions)
    # 2. the edition address is refilled

    # check if edition is registered
    registration = ownership_models.OwnershipRegistration.objects.filter(edition=instance.edition)
    if not registration:
        registration = ownership_models.OwnershipRegistration.create(edition=instance.edition,
                                                                     new_owner=instance.edition.owner)
        registration.save()

    # refill the edition address
    # create the transaction
    refill = BitcoinTransaction.refill(instance)
    # set the loan as the dependent transaction so that it is sent after the refill by the
    # transaction_monitor
    refill.dependent_tx = loan
    refill.save()
    tasks.refill.delay(refill.id, util.mainAdminPassword())


@receiver(loan_piece_created, sender=LoanPieceEndpoint)
def on_loan_piece_create(sender, instance, password, *args, **kwargs):
    # upon loan created we need to check if:
    # 1. If it requires a migration

    # check migration
    migration = check_migration(instance)
    if migration:
        instance.prev_btc_address = migration.new_btc_address
        instance.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(instance, password)
        instance.save()


@receiver(loan_piece_confirm, sender=LoanPieceEndpoint)
def on_loan_piece_confirmed(sender, instance, *args, **kwargs):
    # Create bitcoin consign transaction
    loan_piece = BitcoinTransaction.loan_piece(instance)

    # before pushing the transaction we need to check:
    # 1. the piece is already registered
    # 2. the piece address is refilled

    # check if edition is registered
    # unlike editions a piece is registered at the time of creation

    # refill the piece address
    # create the transaction
    refill = BitcoinTransaction.refill(instance)
    # set the loan as the dependent transaction so that it is sent after the refill by the
    # transaction_monitor
    refill.dependent_tx = loan_piece
    refill.save()
    tasks.refill.delay(refill.id, util.mainAdminPassword())


@receiver(post_save, sender=ownership_models.ConsignedRegistration)
def on_consigned_registration_create(sender, instance, created, *args, **kwargs):
    if created:
        # Create bitcoin transaction
        transaction = BitcoinTransaction.consigned_registration(instance)

        # consigned registeration of a piece
        tasks.consigned_registration.delay(transaction.id, util.mainAdminPassword())


@receiver(post_save, sender=ownership_models.OwnershipMigration)
def on_migration_created(sender, instance, created, *args, **kwargs):
    if created:
        # Create bitcoin transaction
        # we need to check if its for an edition or piece
        if instance.edition:
            transaction = BitcoinTransaction.migrate(instance)
        else:
            transaction = BitcoinTransaction.migrate_piece(instance)

        # migration of a piece or edition
        tasks.migrate.delay(transaction.id, util.mainAdminPassword())


@receiver(check_pending_actions, sender=UserEndpoint)
def execute_pending_actions(sender, user, *args, **kwargs):
    # check for pending actions when a user logins for the first time
    ownership_transfers = ownership_models.OwnershipTransfer.objects.filter(new_owner=user)

    for ownership_transfer in ownership_transfers:
        ownership_transfer.edition.pending_new_owner = None
        ownership_transfer.edition.owner = ownership_transfer.new_owner
        ownership_transfer.edition.save()
        ownership_transfer.save()
        acl = ActionControl.objects.get(user=ownership_transfer.prev_owner,
                                        piece=ownership_transfer.edition.parent,
                                        edition=ownership_transfer.edition)
        acl.acl_withdraw_transfer = False
        acl.acl_unshare = True
        acl.save()

        # create the transaction
        transfer = BitcoinTransaction.transfer(ownership_transfer)

        # before pushing the transaction we need to check:
        # 1. the edition is already registered (because of lazy editions)
        # 2. the edition address is refilled

        # check if edition is registered
        registration = ownership_models.OwnershipRegistration.objects.filter(edition=ownership_transfer.edition)
        if not registration:
            registration = ownership_models.OwnershipRegistration.create(edition=ownership_transfer.edition,
                                                                         new_owner=ownership_transfer.edition.owner)
            registration.save()

        # refill the edition address
        # create the transaction
        refill = BitcoinTransaction.refill(ownership_transfer)
        # set the transfer as the dependent transaction so that it is sent after the refill by the
        # transaction_monitor
        refill.dependent_tx = transfer
        refill.save()
        tasks.refill.delay(refill.id, util.mainAdminPassword())


def get_pubkey():
    netcode = 'XTN' if settings.BTC_TESTNET else 'BTC'
    prv_wallet = BIP32Node.from_master_secret(settings.DJANGO_PYCOIN_ADMIN_PASS, netcode=netcode)
    public_key = prv_wallet.wallet_key(as_private=False)
    main_address = prv_wallet.bitcoin_address()
    return public_key, main_address


def check_pubkey(sender, **kwargs):
    pubkey, main_address = get_pubkey()
    if main_address != settings.BTC_MAIN_WALLET:
        logger.info("Main address is different from BTC_MAIN_WALLET. Please update your settings and re-run migrations")
        return
    try:
        # this is needed because the app may no be initialized yet at this point
        BitcoinWallet = apps.get_model(app_label='bitcoin', model_name='BitcoinWallet')
        wallet = BitcoinWallet.objects.get(id=1)
        if wallet.public_key != pubkey:
            logger.info("Database public key different from wallet public key. Updating public key...")
            wallet.public_key = pubkey
            wallet.save()
        else:
            logger.info("Database public key is correct")
    except ObjectDoesNotExist:
        logger.info("No public key in the database. Creating one...")
        logger.info("Checking for admin user")
        User = apps.get_model(app_label='auth', model_name='User')
        admins = User.objects.filter(is_superuser=True).order_by('date_joined')
        if len(admins) == 0:
            logger.info("No admin user. Creating one...")
            admin = User.objects.create_superuser(username='admin', email='', password='admin')
        else:
            logger.info("Admin user found")
            admin = admins[0]

        wallet = BitcoinWallet.create(admin, public_key=pubkey)
        wallet.id = 1
        wallet.save()
        logger.info("Done")
