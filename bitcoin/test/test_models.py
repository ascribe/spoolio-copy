# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from pycoin.key.BIP32Node import BIP32Node


class TestFederationWallet(object):

    @pytest.mark.django_db
    def test_unspent_property(self):
        from ..models import FederationWallet
        attrs = {'amount': '3', 'confirmations': 1, 'vout': 2, 'txid': 'txid'}
        federation_wallet = FederationWallet.objects.create(**attrs)
        unspent = federation_wallet.unspent
        assert unspent['amount'] == attrs['amount']
        assert unspent['confirmations'] == attrs['confirmations']
        assert unspent['vout'] == attrs['vout']
        assert unspent['txid'] == attrs['txid']


@pytest.mark.django_db
def test_register_piece(ownership_piece_alice,
                        alice_password,
                        djroot_bitcoin_wallet):
    from ..bitcoin_service import BitcoinService
    from ..models import BitcoinTransaction, TX_PENDING
    piece = ownership_piece_alice.piece
    alice = ownership_piece_alice.new_owner
    path, address = piece.bitcoin_path.split(':')
    pycoin_password = alice_password + alice.email
    assert BIP32Node.from_master_secret(
        pycoin_password,
        netcode='XTN').subkey_for_path(path).address() == address
    assert ownership_piece_alice.prev_btc_address is None
    assert ownership_piece_alice.new_btc_address is None
    assert ownership_piece_alice.btc_tx is None
    assert not BitcoinTransaction.objects.exists()
    btc_tx = BitcoinTransaction.register_piece(ownership_piece_alice)
    assert BitcoinTransaction.objects.count() == 1
    btc_tx = BitcoinTransaction.objects.get(pk=btc_tx.pk)
    djroot_address = djroot_bitcoin_wallet.address
    assert btc_tx.ownership.get() == ownership_piece_alice
    assert ownership_piece_alice.prev_btc_address == djroot_address
    assert ownership_piece_alice.new_btc_address == piece.bitcoin_path
    assert ownership_piece_alice.btc_tx == btc_tx
    assert btc_tx.from_address == djroot_address
    assert btc_tx.outputs[0] == (BitcoinService.minDustSize,
                                 piece.hash_as_address_no_metada())
    assert btc_tx.outputs[1] == (BitcoinService.minDustSize,
                                 piece.hash_as_address())
    assert btc_tx.outputs[2] == (BitcoinService.minDustSize, piece.bitcoin_id)
    assert btc_tx.spoolverb == 'ASCRIBESPOOL01PIECE'
    assert btc_tx.status == TX_PENDING


@pytest.mark.django_db
def test_editions(ownership_edition_alice, djroot_bitcoin_wallet):
    from ..bitcoin_service import BitcoinService
    from ..models import BitcoinTransaction, TX_PENDING
    piece = ownership_edition_alice.piece
    assert ownership_edition_alice.prev_btc_address is None
    assert ownership_edition_alice.new_btc_address is None
    assert ownership_edition_alice.btc_tx is None
    assert not BitcoinTransaction.objects.exists()
    btc_tx = BitcoinTransaction.editions(ownership_edition_alice)
    assert BitcoinTransaction.objects.count() == 1
    btc_tx = BitcoinTransaction.objects.get(pk=btc_tx.pk)
    djroot_address = djroot_bitcoin_wallet.address
    assert btc_tx.ownership.get() == ownership_edition_alice
    assert ownership_edition_alice.prev_btc_address == djroot_address
    assert ownership_edition_alice.new_btc_address == piece.bitcoin_path
    assert ownership_edition_alice.btc_tx == btc_tx
    assert btc_tx.from_address == djroot_address
    assert btc_tx.outputs[0] == (BitcoinService.minDustSize,
                                 piece.hash_as_address_no_metada())
    assert btc_tx.outputs[1] == (BitcoinService.minDustSize,
                                 piece.hash_as_address())
    assert btc_tx.outputs[2] == (BitcoinService.minDustSize, piece.bitcoin_id)
    assert btc_tx.spoolverb == 'ASCRIBESPOOL01EDITIONS1'
    assert btc_tx.status == TX_PENDING


@pytest.mark.django_db
def test_loan_piece(loan_piece):
    from ..bitcoin_service import BitcoinService
    from ..models import BitcoinTransaction, TX_PENDING
    piece = loan_piece.piece
    assert loan_piece.prev_btc_address is None
    assert loan_piece.new_btc_address is None
    assert loan_piece.btc_tx is None
    assert not BitcoinTransaction.objects.filter(
        ownership__type='LoanPiece').exists()
    btc_tx = BitcoinTransaction.loan_piece(loan_piece)
    assert BitcoinTransaction.objects.filter(
        ownership__type='LoanPiece').count() == 1
    btc_tx = BitcoinTransaction.objects.get(pk=btc_tx.pk)
    assert btc_tx.ownership.get().pk == loan_piece.pk
    assert loan_piece.prev_btc_address == piece.bitcoin_id
    assert loan_piece.btc_tx == btc_tx
    assert btc_tx.from_address == piece.bitcoin_id
    assert btc_tx.outputs[0] == (BitcoinService.minDustSize,
                                 piece.hash_as_address_no_metada())
    assert btc_tx.outputs[1] == (BitcoinService.minDustSize,
                                 loan_piece.new_btc_address.split(':')[1])
    assert btc_tx.spoolverb == 'ASCRIBESPOOL01LOAN/{}{}'.format(
        loan_piece.datetime_from.strftime('%y%m%d'),
        loan_piece.datetime_to.strftime('%y%m%d')
    )
    assert btc_tx.status == TX_PENDING


@pytest.mark.django_db
def test_to_address():
    from ..models import BitcoinTransaction
    outputs = ((600, '1MDqUXj9uSNQmAY1k8SZDMjFtenBgNTPG9'),
               (600, 'mgcyZY4K1sN11ULPxe2355SpfvXWm6a38P'))
    tx = BitcoinTransaction.objects.create(outputs=outputs)
    assert tx.to_address == outputs[-1][1]


@pytest.mark.django_db
def test_old_address():
    from ..models import BitcoinTransaction
    outputs = ((600, '1MDqUXj9uSNQmAY1k8SZDMjFtenBgNTPG9'),
               (600, 'mgcyZY4K1sN11ULPxe2355SpfvXWm6a38P'))
    tx = BitcoinTransaction.objects.create(outputs=outputs)
    assert tx.old_address == outputs[1][1]


@pytest.mark.django_db
def test_file_hash():
    from ..models import BitcoinTransaction
    outputs = ((600, '1MDqUXj9uSNQmAY1k8SZDMjFtenBgNTPG9'),
               (600, 'mgcyZY4K1sN11ULPxe2355SpfvXWm6a38P'))
    tx = BitcoinTransaction.objects.create(outputs=outputs)
    assert tx.file_hash == (outputs[0][1], outputs[1][1])


@pytest.mark.django_db
def test_edition_num(ownership_edition_alice):
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    ownership_edition_alice.btc_tx = tx
    ownership_edition_alice.save()
    assert tx.edition_num == 0


@pytest.mark.django_db
def test_num_editions(ownership_piece_alice):
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    ownership_piece_alice.btc_tx = tx
    ownership_piece_alice.save()
    assert tx.num_editions == -1


@pytest.mark.django_db
def test_loan_start(loan_piece):
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    loan_piece.btc_tx = tx
    loan_piece.save()
    assert tx.loan_start == loan_piece.datetime_from.strftime('%y%m%d')


@pytest.mark.django_db
def test_loan_end(loan_piece):
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    loan_piece.btc_tx = tx
    loan_piece.save()
    assert tx.loan_end == loan_piece.datetime_to.strftime('%y%m%d')


@pytest.mark.django_db
def test_inputs_getter():
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    assert tx.inputs is None


@pytest.mark.django_db
def test_inputs_setter():
    from ..models import BitcoinTransaction
    tx = BitcoinTransaction.objects.create()
    tx.inputs = ('inputs',)
    assert tx.inputs == ('inputs',)


@pytest.mark.django_db
@pytest.mark.usefixtures('djroot_bitcoin_wallet')
def test_get_wallet_of_alice(alice_bitcoin_wallet):
    from ..models import BitcoinTransaction
    alice = alice_bitcoin_wallet.user
    assert BitcoinTransaction.get_wallet(None, alice) == alice_bitcoin_wallet


@pytest.mark.django_db
def test_get_wallet_of_admin(djroot_bitcoin_wallet):
    from ..models import BitcoinTransaction
    assert BitcoinTransaction.get_wallet(
        djroot_bitcoin_wallet.address, None) == djroot_bitcoin_wallet


@pytest.mark.django_db
def test_from_wallet(djroot_bitcoin_wallet):
    from ..models import BitcoinTransaction
    address = djroot_bitcoin_wallet.address
    tx = BitcoinTransaction.objects.create(from_address=address)
    assert tx.from_wallet == djroot_bitcoin_wallet
