from django.core.management import call_command
from django.utils.six import StringIO

import pytest


@pytest.mark.django_db
def test_create_whitelabel(alice):
    from whitelabel.models import WhitelabelSettings
    out = StringIO()
    call_command(
        'createwhitelabel',
        user_email=alice.email,
        subdomain='xyz',
        whitelabel_name='abc',
        stdout=out,
        logo='http://test.com'
    )
    whitelabel = WhitelabelSettings.objects.get(user__email=alice.email)
    assert whitelabel.user == alice
    assert whitelabel.acl_unconsign is True
    assert whitelabel.acl_edit is True
    assert whitelabel.acl_request_unconsign is True
    assert whitelabel.acl_create_editions is True
    assert whitelabel.acl_wallet_submitted is True
    assert whitelabel.acl_coa is True
    assert whitelabel.acl_download is True
    assert whitelabel.acl_share is True
    assert whitelabel.acl_edit_public_contract is True
    assert whitelabel.acl_transfer is True
    assert whitelabel.acl_view_settings_api is False
    assert whitelabel.acl_withdraw_consign is True
    assert whitelabel.acl_view_powered_by is True
    assert whitelabel.acl_wallet_accepted is True
    assert whitelabel.acl_view is True
    assert whitelabel.acl_wallet_submit is True
    assert whitelabel.acl_withdraw_transfer is True
    assert whitelabel.acl_view_settings_bitcoin is False
    assert whitelabel.acl_view_settings_account_hash is False
    assert whitelabel.acl_consign is True
