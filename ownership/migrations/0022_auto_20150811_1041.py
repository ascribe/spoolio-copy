# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from util import crypto
from django.conf import settings
from bitcoin.models import BitcoinWallet


def most_recent_transfer(apps, edition):
        OwnershipTransfer = apps.get_model("ownership", "OwnershipTransfer")
        # could also calculate this via the chain of bitcoin addresses
        # (and that could be done independently of the DB, using the blockchain)
        # TODO: do we need the exclude? A: yes for btc_owner_address, but might miss some transfers
        transfers = OwnershipTransfer.objects.filter(edition_id=edition.id, type='OwnershipTransfer').exclude(btc_tx=None).order_by("datetime")
        n_transfers = len(transfers)
        if n_transfers > 0:
            return transfers[n_transfers - 1]
        else:
            return None


def btc_owner_address(apps, edition):
    t = most_recent_transfer(apps, edition)
    if t is not None and t.new_btc_address is not None:
        return t.new_btc_address
    else:
        return edition.bitcoin_path


def forwards_func(apps, schema_editor):
    # We need to convert the encoded passwords to encoded wif
    Ownership = apps.get_model("ownership", "Ownership")
    Edition = apps.get_model("piece", "Edition")

    for o in Ownership.objects.filter(ciphertext_password__isnull=False):
        if o.prev_btc_address:
            path, prev_address = o.prev_btc_address.split(':')
        else:
            edition = Edition.objects.get(id=o.edition_id)
            path, prev_address = btc_owner_address(apps, edition).split(':')

        password = crypto.decode(settings.SECRET_KEY, o.ciphertext_password)
        wallet = BitcoinWallet.pycoinWallet(password=BitcoinWallet.pycoinPassword(o.prev_owner, password),
                                            public=False)

        wif = wallet.subkey_for_path(path).wif()
        encoded_wif = crypto.encode(settings.SECRET_KEY, wif)

        o.ciphertext_password = encoded_wif
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0021_auto_20150805_1521'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
        migrations.RenameField(
            model_name='ownership',
            old_name='ciphertext_password',
            new_name='ciphertext_wif',
        ),
    ]
