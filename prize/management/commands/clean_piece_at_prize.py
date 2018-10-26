"""
Clean PieceAtPrize entries that do not have a piece
e.g. piece_at_prize.piece -> DoesNotExist
"""

from prize.models import PieceAtPrize
from piece.models import Piece

from django.core.management.base import NoArgsCommand


def clean_piece_at_prize():
    piece_at_prize_ids = []
    # get bad PieceAtPrize
    for pap in PieceAtPrize.objects.all():
        try:
            pap.piece
        except Piece.DoesNotExist:
            piece_at_prize_ids.append(pap.id)

    # delete bad PieceAtPrize
    for id in piece_at_prize_ids:
        print "Deleting PieceAtPrize with id {}".format(id)
        PieceAtPrize.objects.get(id=id).delete()


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        clean_piece_at_prize()
