# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def test_calc_tx_size():
    from ..bitcoin_service import BitcoinService
    assert BitcoinService.calc_tx_size(2, 3) == 408
