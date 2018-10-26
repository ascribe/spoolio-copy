# Adapted from http://www.codekoala.com/posts/aes-encryption-python-using-pycrypto/
import os
import base64

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


def encode(key, plaintext):
    assert plaintext is not None
    cipher = AES.new(_pad(key))
    ciphertext = base64.b64encode(cipher.encrypt(_pad(plaintext)))
    return ciphertext


def decode(key, ciphertext):
    assert ciphertext is not None
    cipher = AES.new(_pad(key))
    plaintext = cipher.decrypt(base64.b64decode(ciphertext)).rstrip(_PADDING)
    return plaintext


# see http://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
def sign(privkey, plaintext):
    _hash = SHA256.new(plaintext).digest()
    signature = hex(privkey.sign(_hash, '')[0])[2:].upper()
    return _hash, signature


def verify(pubkey, plaintext, signature):
    _hash = SHA256.new(plaintext).digest()
    return pubkey.verify(_hash, (long(signature, 16), None))


def import_env_key(env_name):
    return RSA.importKey(os.environ[env_name].replace('\\n', '\n'))


# the block size for the cipher object; must be 16, 24, or 32 for AES
_BLOCK_SIZE = 32

# the character used for padding--with a block cipher such as AES, the value
# you encrypt must be a multiple of _BLOCK_SIZE in length.  This character is
# used to ensure that your value is always a multiple of _BLOCK_SIZE
_PADDING = '{'


def _pad(plaintext):
    return plaintext + (_BLOCK_SIZE - len(plaintext) % _BLOCK_SIZE) * _PADDING
