import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from ownership.models import OwnershipPiece, OwnershipEditions, OwnershipTransfer, Consignment, Loan
from ownership.models import LoanPiece, Share, SharePiece
from ownership.signals import safe_delete, transfer_user_needs_to_register, consignment_confirmed, consignment_denied, \
    share_delete
from ownership.signals import consignment_withdraw, unconsignment_create
from ownership.api import TransferEndpoint, ConsignEndpoint, UnConsignEndpoint
from piece.models import PieceFactory, Edition
from piece.signals import editions_bulk_create
from acl.models import ActionControl

logger = logging.getLogger(__name__)


# set the acl for the piece upon creation
@receiver(post_save, sender=OwnershipPiece)
def on_ownership_piece_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_piece_create')
        ActionControl.set_acl_registree_piece(piece=instance.piece, user=instance.new_owner)


# set the acl for the edition upon creation
@receiver(editions_bulk_create, sender=PieceFactory)
def on_editions_create(sender, user_registered, editions, *args, **kwargs):
    logger.info('SIGNAL on_editions_create')
    for edition in editions:
        db_edition = Edition.objects.get(bitcoin_path=edition.bitcoin_path)
        ActionControl.set_acl_registree_edition(user=user_registered, edition=db_edition)


# set the acl for the parent piece once the editions are created
@receiver(post_save, sender=OwnershipEditions)
def on_ownership_editions_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownersip_editions_create')
        for acl in ActionControl.objects.filter(piece=instance.piece, edition=None):
            # NOTE: This could be redundant to ActionControl.set_acl_registree_edition
            acl.acl_create_editions = False
            acl.save()


# set acl for transferee and prev owner on ownership transfer create
@receiver(post_save, sender=OwnershipTransfer)
def on_ownership_transfer_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_transfer_create')
        ActionControl.set_acl_transferee(edition=instance.edition, user=instance.new_owner)
        ActionControl.set_acl_prev_owner(edition=instance.edition, user=instance.prev_owner)
        # set edit to false
        for acl in ActionControl.objects.filter(piece=instance.edition.parent):
            acl.acl_edit = False
            acl.save()


# set acl for prev_owner on ownership transfer withdraw
@receiver(post_delete, sender=OwnershipTransfer)
def on_ownership_transfer_withdraw(sender, instance, *args, **kwargs):
    logger.info('SIGNAL on_ownership_transfer_withdraw')
    ActionControl.set_acl_transferee(edition=instance.edition, user=instance.prev_owner)
    ActionControl.objects.get(user=instance.new_owner,
                              piece=instance.edition.parent,
                              edition=instance.edition).delete()


# set acl for transferer on transfer to a user that needs to register
@receiver(transfer_user_needs_to_register, sender=TransferEndpoint)
def on_transfer_user_needs_to_register(sender, prev_owner, edition, *args, **kwargs):
    logger.info('SIGNAL on_transfer_user_needs_to_register')
    acl = ActionControl.objects.get(user=prev_owner, piece=edition.parent, edition=edition)
    acl.acl_withdraw_transfer = True
    acl.acl_unshare = False
    acl.save()


# set acl for consignee and owner on ownership consignment create
@receiver(post_save, sender=Consignment)
def on_ownership_consignment_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_consignment_create')
        ActionControl.set_acl_consignee(edition=instance.edition, user=instance.new_owner)
        ActionControl.set_acl_owner(edition=instance.edition, user=instance.prev_owner)


# set acl for consigner when a consignment is confirmed
@receiver(consignment_confirmed, sender=ConsignEndpoint)
def on_consignment_confirm(sender, instance, *args, **kwargs):
    logger.info('SIGNAL on_consignment_confirm')
    # set the acl for consigner
    acl = ActionControl.objects.get(user=instance.prev_owner, piece=instance.edition.parent,
                                    edition=instance.edition)
    acl.acl_withdraw_consign = False
    acl.acl_request_unconsign = True
    acl.save()

    # set acl for consignee
    acl = ActionControl.objects.get(user=instance.new_owner, edition=instance.edition)
    acl.acl_loan = True
    acl.acl_transfer = True
    acl.acl_unconsign = True
    acl.save()


# set acl when a consignment is denied
@receiver(consignment_denied, sender=ConsignEndpoint)
def on_consignment_denied(sender, prev_owner, new_owner, edition, *args, **kwargs):
    logger.info('SIGNAL on_consignment_denied')
    ActionControl.objects.get(user=new_owner, piece=edition.parent, edition=edition).delete()
    ActionControl.set_acl_transferee(user=prev_owner, edition=edition)


# set acl when a consignment is withdrawn
@receiver(consignment_withdraw, sender=ConsignEndpoint)
def on_consignment_withdraw(sender, prev_owner, new_owner, edition, *args, **kwargs):
    logger.info('SIGNAL on_consignment_withdraw')
    ActionControl.objects.get(user=new_owner, piece=edition.parent, edition=edition).delete()
    ActionControl.set_acl_transferee(user=prev_owner, edition=edition)


# set acl when a unconsignment is created
@receiver(unconsignment_create, sender=UnConsignEndpoint)
def on_unconsignment_create(sender, instance, *args, **kwargs):
    logger.info('SIGNAL on_unconsignment_create')
    # set acl for unconsignee
    ActionControl.objects.get(user=instance.prev_owner, piece=instance.edition.parent,
                              edition=instance.edition).delete()
    # set acl for owner
    ActionControl.set_acl_transferee(user=instance.edition.owner, edition=instance.edition)


# set acl for loanee on ownership loan create
@receiver(post_save, sender=Loan)
def on_ownership_loan_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_loan_create')
        ActionControl.set_acl_sharee(edition=instance.edition, user=instance.new_owner)


# set acl for loanee on ownership loan piece create
@receiver(post_save, sender=LoanPiece)
def on_ownership_loan_piece_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_loan_piece_create')
        ActionControl.set_piece_acl_sharee(piece=instance.piece, user=instance.new_owner)


# set acl for sharee on ownership share create
@receiver(post_save, sender=Share)
def on_ownership_share_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_share_create')
        ActionControl.set_acl_sharee(edition=instance.edition, user=instance.new_owner)


# set acl for sharee on ownership share delete
@receiver(safe_delete, sender=Share)
def on_ownership_share_delete(sender, instance, *args, **kwargs):
    logger.info('SIGNAL on_ownership_share_delete')
    acl = ActionControl.objects.get(user=instance.new_owner, piece=instance.piece, edition=instance.edition)
    acl.acl_view = False
    acl.acl_loan_request = False
    acl.save()


# set acl for sharee on ownership share without safe_delete
# if edition == None then set the acl_view of all editions to False!
@receiver(share_delete, sender=Share)
def on_ownership_share_delete(sender, user, piece, edition, *args, **kwargs):
    logger.info('SIGNAL on_ownership_share_delete')
    ActionControl.objects \
        .filter(user=user,
                piece=piece,
                edition=edition) \
        .update(acl_view=False,
                acl_loan_request=False)
    if edition is None:
        # if no edition is given set the acl_view of all editions to False!
        ActionControl.objects \
            .filter(user=user,
                    piece=piece) \
            .update(acl_view=False,
                    acl_loan_request=False)


# set acl for sharee on ownership share piece create
@receiver(post_save, sender=SharePiece)
def on_ownership_share_piece_create(sender, instance, created, *args, **kwargs):
    if created:
        logger.info('SIGNAL on_ownership_share_piece_create')
        ActionControl.set_piece_acl_sharee(piece=instance.piece, user=instance.new_owner)


# set acl for sharee on ownership share piece delete
@receiver(safe_delete, sender=SharePiece)
def on_ownership_share_piece_delete(sender, instance, *args, **kwargs):
    logger.info('SIGNAL on_ownership_share_piece_delete')
    # also set the acl_view of all editions to False!
    ActionControl.objects \
        .filter(user=instance.new_owner,
                piece=instance.piece) \
        .update(acl_view=False,
                acl_loan_request=False)
