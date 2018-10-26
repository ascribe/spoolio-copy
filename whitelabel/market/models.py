from whitelabel.models import WhitelabelSettings


class WhitelabelMarketFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create(user, subdomain, name=None, title=None, logo=None, head=None):
        if name is None:
            name = subdomain

        if title is None:
            title = name

        market = WhitelabelSettings(user=user, subdomain=subdomain, name=name, title=title, logo=logo, head=head)

        market.acl_delete = False
        market.acl_edit = True
        market.acl_view = True
        market.acl_download = True

        market.acl_create_piece = True
        market.acl_view_editions = True
        market.acl_create_editions = True

        market.acl_coa = True

        market.acl_unshare = False
        market.acl_share = True

        market.acl_transfer = True
        market.acl_withdraw_transfer = True

        market.acl_loan_request = False
        market.acl_loan = False

        market.acl_consign = True
        market.acl_withdraw_consign = True
        market.acl_request_unconsign = True
        market.acl_unconsign = True

        market.acl_wallet_accepted = True
        market.acl_wallet_submit = True
        market.acl_wallet_submitted = True

        market.acl_view_settings_contract = True
        market.acl_edit_public_contract = True
        market.acl_update_public_contract = False
        market.acl_edit_private_contract = False
        market.acl_update_private_contract = False
        market.acl_create_contractagreement = False

        market.acl_intercom = True
        market.acl_view_powered_by = True
        market.acl_view_settings_account = True
        market.acl_view_settings_account_hash = False
        market.acl_view_settings_api = False
        market.acl_view_settings_bitcoin = False
        market.acl_view_settings_copyright_association = False
        market.save()
        return market
