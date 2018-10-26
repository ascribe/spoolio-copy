# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii

from Crypto.PublicKey import RSA

import pytest


@pytest.fixture
def rsa_extern_key():
    return (
        '-----BEGIN RSA PRIVATE KEY-----\n'
        'MIICWwIBAAKBgQCgmiPj/R9eb+AIbyau/u3PslXJ7dkVGegT3TD0Mr8lYh1/lpsN\n'
        'nEh0Z52Bsp3/64E2U5Vg5SjmiNjXBPHn0AOplt2gUbJUKT0aN+lVTbVke8HG46SS\n'
        'NZKcc3gv6z5BeBgpIl9BLvhIotqIcUkrPBlxr6CTudPpRQ0oYQO90nShHQIDAQAB\n'
        'AoGAJWfBNDigNb6Yz14UBG4btWQz1vQuu1ttUjMSU8399xcDB9RsCJ99wJ7hcHPJ\n'
        'mPGhBqYxBIBbJlZ5KptcPEGWmGqg80CctKkE++ouBWB5j6yCiQAssLpklJk+VJGS\n'
        'Fez0XUxUG5ThbX9s4LJ9juL9DteTkV5MLYT7b8SKBYYgOAECQQDCRk3hCoi2XXgE\n'
        'fAESSlFOF0t/Ml1wrp5bDjRlkdlWOmhE4TLy4Ns7WDSKc6tYvGQgF6S69fxudysX\n'
        'mQwAqnQRAkEA06EEmBpKAs/8pZMsRit5lXpbJUo1L97pM3e0aadzazhIGU87Km5U\n'
        's9AlOHCURennHBtMncSArRxZmPNhlQw4TQJADrQDcOS7NBIe4zf/XMMDJEXfEOFe\n'
        '8QhGM93/WTCQolYJTi09DeS2sucaEuBuN2kKquMfNIcpc7LRMBgFMIe2AQJAWhph\n'
        'OV1gC4iAOgLKQ+n4rzLUIbFRqdsPkPEzaBR6aLkiwVvhhfRJrfE+F6SfDJFE68uX\n'
        'uEhUvN+oKh3dezcjtQJATRQmoGjXOvJQGWXQZdNPjPghjtutewcebSSpR7ENeUNI\n'
        'BfrvYto9E0rih1znsogs0T4/SVAAsaIIn6fPjlJz4A==\n'
        '-----END RSA PRIVATE KEY-----'
    )


@pytest.fixture
def rsa_key(rsa_extern_key):
    return RSA.importKey(rsa_extern_key)


@pytest.fixture
def message():
    return 'Mr Jobs*iTunes*2/4*2013*2015Mar11-15:15:52'


@pytest.fixture
def message_signature():
    return (
        'A07153E631889CCA2CBBC0FAB8366B680CB83E808EE5A601EC33F9CABAB3DCD8AD482'
        'A0A4E3E7E623F71639AFA88C42525DF4629FF044B9D0668D12410731C1B07720B36F5'
        '38C878D78AF1F40DA93D26AB01D93C7F8C223ECDA54B923E8D6EFE7557E513A3524B1'
        'C49D54CD6183D28CAF42F8C398EB234F338E1B0123A9E8040L'
    )


@pytest.fixture
def message_hash_hexdigest():
    return '3d3aa1152c1144e924f0af97d512ed29910296e8e424a3d711a656f215f83d6a'


@pytest.fixture
def message_hash_bindigest(message_hash_hexdigest):
    return binascii.unhexlify(message_hash_hexdigest)


def test_verify(rsa_key, message, message_signature):
    from ..crypto import verify
    assert verify(rsa_key.publickey(), message, message_signature)


def test_sign(rsa_key, message, message_signature, message_hash_hexdigest):
    from ..crypto import sign
    hash_bindigest, signature = sign(rsa_key, message)
    assert binascii.hexlify(hash_bindigest) == message_hash_hexdigest
    assert signature == message_signature


def test_encode():
    from ..crypto import encode
    ciphertext = encode(b'key', 'plaintext')
    assert ciphertext


def test_decode():
    from ..crypto import decode
    plaintext = decode(b'key', 'yTDXRiK1YOlCfQuU2Bn6xHRMRc8aR2hI0GrA4B6+sQ4=')
    assert plaintext == 'plaintext'
