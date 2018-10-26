from whitelabel.models import WhitelabelSettings


class WhitelabelIkonotvFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create(user):
        path = 'https://s3-us-west-2.amazonaws.com/ascribe0/whitelabel/ikonotv/'
        logo = path + 'ikono-logo-black.png'
        head = {
            "meta": {
                "ms1": {
                    "name": "msapplication-TileColor",
                    "content": "#da532c"
                },
                "ms2": {
                    "name": "msapplication-TileImage",
                    "content": path + "mstile-144x144.png"
                },
                "ms3": {
                    "name": "theme-color",
                    "content": "#ffffff"
                }
            },
            "link": {
                "apple1": {"rel": "apple-touch-icon", "sizes": "57x57",
                           "href": path + "apple-touch-icon-57x57.png"},
                "apple2": {"rel": "apple-touch-icon", "sizes": "60x60",
                           "href": path + "apple-touch-icon-60x60.png"},
                "apple3": {"rel": "apple-touch-icon", "sizes": "72x72",
                           "href": path + "apple-touch-icon-72x72.png"},
                "apple4": {"rel": "apple-touch-icon", "sizes": "76x76",
                           "href": path + "apple-touch-icon-76x76.png"},
                "apple5": {"rel": "apple-touch-icon", "sizes": "114x114",
                           "href": path + "apple-touch-icon-114x114.png"},
                "apple6": {"rel": "apple-touch-icon", "sizes": "120x120",
                           "href": path + "apple-touch-icon-120x120.png"},
                "apple7": {"rel": "apple-touch-icon", "sizes": "144x144",
                           "href": path + "apple-touch-icon-144x144.png"},
                "apple8": {"rel": "apple-touch-icon", "sizes": "152x152",
                           "href": path + "apple-touch-icon-152x152.png"},
                "apple9": {"rel": "apple-touch-icon", "sizes": "180x180",
                           "href": path + "apple-touch-icon-180x180.png"},
                "icon1": {"rel": "icon", "type": "image/png",
                          "href": path + "favicon-32x32.png",
                          "sizes": "32x32"},
                "icon2": {"rel": "icon", "type": "image/png",
                          "href": path + "favicon-96x96.png",
                          "sizes": "96x96"},
                "icon3": {"rel": "icon", "type": "image/png",
                          "href": path + "favicon-16x16.png",
                          "sizes": "16x16"},
                "icon4": {"rel": "icon", "type": "image/png",
                          "href": path + "android-chrome-192x192.png",
                          "sizes": "192x192"},
                "manifest": {"rel": "manifest",
                             "href": path + "manifest.json"}
            }
        }
        market = WhitelabelSettings(user=user,
                                    subdomain='ikonotv',
                                    name='IkonoTV',
                                    title='Ikono TV',
                                    logo=logo,
                                    head=head)

        market.acl_delete = False
        market.acl_edit = True
        market.acl_view = True
        market.acl_download = True

        market.acl_create_piece = True
        market.acl_view_editions = False
        market.acl_create_editions = False

        market.acl_coa = False

        market.acl_unshare = False
        market.acl_share = True

        market.acl_transfer = False
        market.acl_withdraw_transfer = False

        market.acl_loan_request = True
        market.acl_loan = True

        market.acl_consign = False
        market.acl_withdraw_consign = False
        market.acl_request_unconsign = False
        market.acl_unconsign = False

        market.acl_wallet_accepted = True
        market.acl_wallet_submit = True
        market.acl_wallet_submitted = True

        market.acl_view_settings_contract = True
        market.acl_edit_public_contract = False
        market.acl_update_public_contract = False
        market.acl_edit_private_contract = True
        market.acl_update_private_contract = False
        market.acl_create_contractagreement = True

        market.acl_intercom = True
        market.acl_view_powered_by = True
        market.acl_view_settings_account = True
        market.acl_view_settings_account_hash = False
        market.acl_view_settings_api = False
        market.acl_view_settings_bitcoin = False
        market.acl_view_settings_copyright_association = True
        market.save()
        return market
