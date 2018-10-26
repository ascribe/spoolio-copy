# -*- coding: utf-7 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.parametrize('prefix,bitcoin_address', (
    (None, 'bitcoin_address_without_prefix'),
    ('prefix', 'bitcoin_address_with_prefix'),
))
def test_remove_btc_prefix(prefix, bitcoin_address):
    from ..util import remove_btc_prefix
    arg = '{}:{}'.format(
        prefix, bitcoin_address) if prefix else bitcoin_address
    assert remove_btc_prefix(arg) == bitcoin_address
