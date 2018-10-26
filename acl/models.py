from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist


class ActionControlFieldsMixin(models.Model):
    acl_view = models.BooleanField(default=False)
    acl_edit = models.BooleanField(default=False)
    acl_download = models.BooleanField(default=False)
    acl_delete = models.BooleanField(default=False)
    acl_create_editions = models.BooleanField(default=False)
    acl_view_editions = models.BooleanField(default=True)
    acl_share = models.BooleanField(default=False)
    acl_unshare = models.BooleanField(default=False)
    acl_transfer = models.BooleanField(default=False)
    acl_withdraw_transfer = models.BooleanField(default=False)
    acl_consign = models.BooleanField(default=False)
    acl_withdraw_consign = models.BooleanField(default=False)
    acl_unconsign = models.BooleanField(default=False)
    acl_request_unconsign = models.BooleanField(default=False)
    acl_loan = models.BooleanField(default=False)
    acl_coa = models.BooleanField(default=False)
    acl_loan_request = models.BooleanField(default=False)

    class Meta:
        abstract = True


class UserActionControlFieldsMixin(models.Model):
    acl_view_settings_bitcoin = models.BooleanField(default=True)
    acl_view_settings_account = models.BooleanField(default=True)
    acl_view_settings_account_hash = models.BooleanField(default=True)
    acl_view_settings_api = models.BooleanField(default=True)
    acl_view_settings_contract = models.BooleanField(default=True)

    acl_create_piece = models.BooleanField(default=True)

    acl_edit_private_contract = models.BooleanField(default=False)
    acl_update_private_contract = models.BooleanField(default=False)

    acl_edit_public_contract = models.BooleanField(default=False)
    acl_update_public_contract = models.BooleanField(default=False)

    acl_create_contractagreement = models.BooleanField(default=False)

    acl_intercom = models.BooleanField(default=True)

    class Meta:
        abstract = True


class ActionControl(ActionControlFieldsMixin, models.Model):
    user = models.ForeignKey(User, related_name='acl_user')
    piece = models.ForeignKey('piece.Piece', related_name="acl_at_piece", blank=True, null=True)
    edition = models.ForeignKey('piece.Edition', related_name="acl_at_edition", blank=True, null=True)

    datetime = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_items_for_user(user, acl_filter={}, classname='piece'):
        # extend optional acl with default view filter
        acl_filter = dict({'acl_view': True}, **acl_filter)
        acl_filter = {'acl_at_{}__{}'.format(classname, k): v for k, v in acl_filter.iteritems()}

        if classname == 'piece':
            from piece.models import Piece
            return Piece.objects.filter(acl_at_piece__user=user, datetime_deleted=None, **acl_filter).distinct()
        elif classname == 'edition':
            from piece.models import Edition
            return Edition.objects.filter(acl_at_edition__user=user, datetime_deleted=None, **acl_filter).distinct()
        else:
            return None

    @staticmethod
    def get_acl_edition_user(edition, user):
        return ActionControl.objects.get(user=user, edition=edition)

    # OwnershipPiece create
    @staticmethod
    def set_acl_registree_piece(piece, user):
        acl = ActionControl(user=user, piece=piece, edition=None)

        acl.acl_view = True
        acl.acl_edit = True
        acl.acl_download = True
        acl.acl_delete = True
        acl.acl_create_editions = True
        acl.acl_share = True
        acl.acl_unshare = False
        acl.acl_transfer = False
        acl.acl_withdraw_transfer = False
        acl.acl_consign = False
        acl.acl_withdraw_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = True
        acl.acl_coa = False
        acl.save()

    # OwnershipEditions create
    @staticmethod
    def set_acl_registree_edition(edition, user):
        acl = ActionControl(user=user, piece=edition.parent, edition=edition)

        acl.acl_view = True
        acl.acl_edit = True
        acl.acl_download = True
        acl.acl_delete = True
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = False
        acl.acl_transfer = True
        acl.acl_withdraw_transfer = False
        acl.acl_consign = True
        acl.acl_withdraw_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = True
        acl.acl_coa = True
        acl.save()

    # OwnershipTransfer create
    @staticmethod
    def set_acl_transferee(edition, user):
        try:
            acl = ActionControl.objects.get(user=user, piece=edition.parent, edition=edition)
        except ObjectDoesNotExist:
            acl = ActionControl(user=user, piece=edition.parent, edition=edition)

        acl.acl_view = True
        acl.acl_edit = False
        acl.acl_download = True
        acl.acl_delete = True
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = False
        acl.acl_transfer = True
        acl.acl_withdraw_transfer = False
        acl.acl_consign = True
        acl.acl_withdraw_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = True
        acl.acl_coa = True
        acl.save()

    @staticmethod
    def set_acl_prev_owner(edition, user):
        acl = ActionControl.objects.get(user=user, piece=edition.parent, edition=edition)

        acl.acl_view = True
        acl.acl_edit = False
        acl.acl_download = True
        acl.acl_delete = False
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = True
        acl.acl_transfer = False
        acl.acl_withdraw_transfer = False
        acl.acl_consign = False
        acl.acl_withdraw_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = False
        acl.acl_coa = False
        acl.save()

    # Ownership Consginment create
    @staticmethod
    def set_acl_consignee(edition, user):
        try:
            acl = ActionControl.objects.get(user=user, piece=edition.parent, edition=edition)
        except ObjectDoesNotExist:
            acl = ActionControl(user=user, piece=edition.parent, edition=edition)

        acl.acl_view = True
        acl.acl_edit = False
        acl.acl_download = True
        acl.acl_delete = False
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = False
        acl.acl_transfer = False
        acl.acl_withdraw_transfer = False
        acl.acl_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = False
        acl.acl_coa = False
        acl.save()

    @staticmethod
    def set_acl_owner(edition, user):
        acl = ActionControl.objects.get(user=user, piece=edition.parent, edition=edition)

        acl.acl_view = True
        acl.acl_edit = False
        acl.acl_download = True
        acl.acl_delete = False
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = False
        acl.acl_transfer = False
        acl.acl_withdraw_transfer = False
        acl.acl_consign = False
        acl.acl_withdraw_consign = True
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = False
        acl.acl_coa = False
        acl.save()

    # Ownership Share create
    @staticmethod
    def set_acl_sharee(edition, user):
        try:
            acl = ActionControl.objects.get(user=user, piece=edition.parent, edition=edition)
        except ObjectDoesNotExist:
            acl = ActionControl(user=user, piece=edition.parent, edition=edition)

            acl.acl_view = True
            acl.acl_edit = False
            acl.acl_download = True
            acl.acl_delete = False
            acl.acl_create_editions = False
            acl.acl_share = True
            acl.acl_unshare = True
            acl.acl_transfer = False
            acl.acl_withdraw_transfer = False
            acl.acl_consign = False
            acl.acl_withdraw_consign = False
            acl.acl_unconsign = False
            acl.acl_request_unconsign = False
            acl.acl_loan = False
            acl.acl_coa = False
            acl.acl_loan_request = True
            acl.save()

    @staticmethod
    def set_piece_acl_sharee(piece, user):
        try:
            acl = ActionControl.objects.get(user=user, piece=piece, edition=None)
        except ObjectDoesNotExist:
            acl = ActionControl(user=user, piece=piece, edition=None)

        acl.acl_view = True
        acl.acl_edit = False
        acl.acl_download = True
        acl.acl_delete = False
        acl.acl_create_editions = False
        acl.acl_share = True
        acl.acl_unshare = True
        acl.acl_transfer = False
        acl.acl_withdraw_transfer = False
        acl.acl_consign = False
        acl.acl_withdraw_consign = False
        acl.acl_unconsign = False
        acl.acl_request_unconsign = False
        acl.acl_loan = False
        acl.acl_coa = False
        acl.acl_loan_request = True
        acl.save()


def acl_piece_user(piece, user):
    acl = []

    if not user or isinstance(user, AnonymousUser):
        return acl

    """ edit additional details """
    if (user == piece.user_registered) \
            and (piece.editions < 1 or \
            (all((e._most_recent_transfer is None) for e in piece.editions))):
        acl += ['edit']

    if (piece.num_editions < 1) and (user == piece.user_registered):
        acl += ['editions']

    """ share, download, view """
    acl += ["share", "download", "view"]

    """ unshare """
    from ownership.models import SharePiece
    if len(SharePiece.objects.filter(new_owner=user, piece=piece, datetime_deleted=None)):
        acl += ["unshare"]
    return acl


def acl_edition_user(edition, user):
    acl = []

    if not user or isinstance(user, AnonymousUser):
        return acl

    from piece.models import Edition
    """ edit additional details """
    if all(s._most_recent_transfer is None for s in Edition.objects.filter(parent=edition.parent)) \
            and (user == edition.owner):
        acl += ['edit']

    """ consign """
    if (edition.owner.username == user.username
        and edition.pending_new_owner is None
        and edition.consignee is None):
        acl += ["consign"]

    """ unconsign """
    if edition.consignee == user and edition.consign_status == settings.CONSIGNED:
        acl += ["unconsign"]

    """ transfer """
    if "consign" in acl \
            or (edition.consignee == user
                and edition.consign_status in [settings.CONSIGNED, settings.PENDING_UNCONSIGN]):
        acl += ["transfer"]

    if edition.owner.username == user.username and edition.pending_new_owner is not None:
        acl += ["withdraw_transfer"]

    """ loan """
    if "transfer" in acl:
        acl += ["loan"]

    """ share, download, view """
    acl += ["share", "download", "view"]

    """ unshare """
    from ownership.models import Share
    if len(Share.objects.filter(new_owner=user, edition=edition, datetime_deleted=None)):
        acl += ["unshare"]

    """ delete """
    if edition.owner.username == user.username and edition.pending_new_owner is None:
        acl += ["delete"]

    """ coa """
    if edition.owner.username == user.username and edition.pending_new_owner is None:
        acl += ["coa"]
    return acl

