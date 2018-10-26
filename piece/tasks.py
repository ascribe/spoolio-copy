from __future__ import absolute_import

import logging

from django.contrib.auth import get_user_model
from celery import chain, group

from util.celery import app
from bitcoin.models import BitcoinWallet
from bitcoin.tasks import import_address
from ownership.models import OwnershipEditions
from piece.signals import editions_bulk_create
from piece.models import Edition, Piece, PieceFactory


logger = logging.getLogger('tasks')


@app.task(bind=True)
def handle_edition_creation_error(self, uuid):
    result = self.app.AsyncResult(uuid)
    logger.info('Task {0} raised exception: {1!r}\n{2!r}'.format(
                uuid, result.result, result.traceback))


def register_editions(root_piece, user, num_editions):
    root_piece.num_editions = num_editions
    root_piece.save()
    # To keep compatibility with the old edition creation, we first
    # set the number of editions to 0 for the piece.
    return chain(init_edition_creation.si(root_piece.id),
                 # In this group, we then create each edition
                 # individually and return the actual edition
                 # object back to the group.
                 group(
                     chain(
                         # To create an edition, we first generate a
                         # blockchain address and pass it in a callback
                         create_address.si(user.id),
                         # to import_address to import it into the blockchain
                         # daemon.
                         import_address.s(user.email),
                         init_edition.s(root_piece.id, edition_number + 1, user.id)
                     )
                     for edition_number in range(num_editions)
                 ),
                 # Once the group finishes, all editions created are passed
                 # to finish_edition_creation to bulk_save them into the
                 # database.
                 bulk_create_and_freeze_editions.s(root_piece.id, user.id))


@app.task(ignore_result=True)
def init_edition_creation(piece_id):
    root_piece = Piece.objects.get(pk=piece_id)

    # In order to notify clients that editions are currently created
    # we set the piece's num_editions to 0
    root_piece.num_editions = 0
    root_piece.save()


@app.task(ignore_result=False)
def create_address(user_id):
    user = get_user_model().objects.get(pk=user_id)
    return BitcoinWallet.walletForUser(user).create_new_address()


@app.task(ignore_result=False)
def init_edition(address, piece_id, edition_number, user_id):
    root_piece = Piece.objects.get(pk=piece_id)
    user = get_user_model().objects.get(pk=user_id)
    address = BitcoinWallet.walletForUser(user).create_new_address()
    return Edition(parent=root_piece, edition_number=edition_number, bitcoin_path=address, owner=user)


@app.task(ignore_result=False)
def bulk_create_and_freeze_editions(editions, piece_id, user_id):
    root_piece = Piece.objects.get(pk=piece_id)
    user = get_user_model().objects.get(pk=user_id)

    if not isinstance(editions, (list, tuple)):
        editions = [editions]

    num_editions = len(editions)

    # Depending on how many editions we're creating, bulk_create could potentially be blocking.
    # As we're not delivering the editions to the user right away anyways, we can put this in
    # a task to not block other users of our service.
    Edition.objects.bulk_create(editions)
    # As Django's bulk_create doesn't trigger a post_save signal, we trigger it here
    # manually to trigger setting the ACLs of the editions
    editions_bulk_create.send(sender=PieceFactory, user_registered=user, editions=editions)

    # Since edition creation was completed successfully, we set the num_editions for piece
    # to its actual count
    root_piece.num_editions = num_editions
    root_piece.save()

    # An OwnershipEditions object can only be invoked after setting num_editions of
    # piece back to its original count, as it triggers triggers a Django signal
    # for writing this information also in the blockchain.
    ownership_editions = OwnershipEditions.create(edition=root_piece, new_owner=user)
    ownership_editions.save()

    logger.info('created {} editions in db'.format(num_editions))
    return editions
