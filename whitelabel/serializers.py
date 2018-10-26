from django.conf import settings
from rest_framework import serializers
from core.serializers import SubdomainSerializerMixin
from ownership.models import LoanPiece, ContractAgreement
from whitelabel.models import WhitelabelSettings


class WhitelabelSubdomainSerializerMixin(SubdomainSerializerMixin):
    @property
    def whitelabel_settings(self):
        try:
            return WhitelabelSettings.objects.get(subdomain=self.subdomain)
        except WhitelabelSettings.DoesNotExist:
            return None


class WhitelabelMarketplaceSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    head = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.email

    def get_head(self, obj):
        return obj.head

    class Meta:
        model = WhitelabelSettings


def get_acl_user_submit_piece_by_loan_and_publiccontract(user, subdomain=None, whitelabel_settings=None):
    if subdomain and (whitelabel_settings is None):
        whitelabel_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    is_admin = whitelabel_settings.user == user
    can_submit = not is_admin

    return {'acl_create_piece': not is_admin,
            'acl_loan': not is_admin,
            'acl_edit_public_contract': is_admin,
            'acl_view_settings_contract': is_admin,
            'acl_wallet_submit': can_submit}


def get_acl_user_submit_piece_by_loan_and_contractagreement(user, subdomain=None, whitelabel_settings=None):
    if subdomain and (whitelabel_settings is None):
        whitelabel_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    is_admin = whitelabel_settings.user == user
    can_submit = not is_admin
    # don't allow a submit if there is no accepted or pending contractagreement
    if not ContractAgreement.objects.filter(signee=user,
                                            contract__issuer=whitelabel_settings.user,
                                            datetime_deleted=None,
                                            datetime_rejected=None).exists():
        can_submit = False

    return {'acl_create_piece': not is_admin,
            'acl_loan': not is_admin,
            'acl_create_contractagreement': is_admin,
            'acl_edit_private_contract': is_admin,
            'acl_view_settings_contract': is_admin,
            'acl_wallet_submit': can_submit}


def get_acl_submit_piece_by_loan(piece, user, subdomain=None, whitelabel_settings=None):
    if subdomain and (whitelabel_settings is None):
        whitelabel_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    acl = piece.acl(user).__dict__
    loans = LoanPiece.objects.filter(piece=piece,
                                     new_owner=whitelabel_settings.user,
                                     prev_owner=user,
                                     datetime_deleted=None).exclude(status=0)
    pending_loans = loans.filter(status=None)
    accepted_loans = loans.filter(status=1)
    acl['acl_wallet_submit'] = (piece.user_registered == user and len(loans) == 0 and user != whitelabel_settings.user)
    acl['acl_wallet_submitted'] = len(pending_loans) > 0
    acl['acl_wallet_accepted'] = len(accepted_loans) > 0
    # edit might be needed because of further details (bio & concept)
    # edit can be always true, since the user cannot edit his further details on cyland
    acl['acl_edit'] = acl['acl_wallet_submit']

    return acl


def get_acl_user_submit_edition_by_consign(user, subdomain=None, whitelabel_settings=None):
    if subdomain and (whitelabel_settings is None):
        whitelabel_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    is_admin = whitelabel_settings.user == user

    # The ACLs of the market are set on a user basis (admin or submittee)
    return {'acl_create_piece': not is_admin,
            'acl_wallet_submit': not is_admin,
            'acl_transfer': is_admin,
            'acl_consign': not is_admin,
            'acl_edit_public_contract': is_admin,
            'acl_update_public_contract': is_admin,
            'acl_view_settings_contract': is_admin}


def get_acl_submit_edition_by_consign(edition, user, subdomain=None, whitelabel_settings=None):
    if subdomain and (whitelabel_settings is None):
        whitelabel_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    acl = edition.acl(user).__dict__
    acl['acl_wallet_submit'] = (edition.owner == user and
                                edition.consign_status == settings.NOT_CONSIGNED)
    acl['acl_wallet_submitted'] = (edition.owner == user and
                                   edition.consign_status == settings.PENDING_CONSIGN and
                                   edition.consignee == whitelabel_settings.user)
    acl['acl_wallet_accepted'] = (edition.owner == user and
                                  edition.consign_status == settings.CONSIGNED and
                                  edition.consignee == whitelabel_settings.user)
    # edit might be needed because of further details (bio & concept)
    # edit can be always true, since the user cannot edit his further details on cyland
    # TODO Review this. For the sake of issue #70, will comment it out. See
    # https://github.com/ascribe/spoolio/issues/70
    # acl['acl_edit'] = acl['acl_wallet_submit']

    return acl
