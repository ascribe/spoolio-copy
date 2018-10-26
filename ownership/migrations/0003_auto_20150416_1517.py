# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0002_auto_20150416_1439'),
        ('bitcoin', '0002_bitcoinwallet')
    ]

    operations = [
        migrations.AlterField(
            model_name='ownership',
            name='btc_tx',
            field=models.ForeignKey(blank=True, to='bitcoin.BitcoinTransaction', null=True),
            preserve_default=True,
        ),
    ]
