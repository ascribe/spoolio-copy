# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0004_federationwallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitcointransaction',
            name='dependent_tx',
            field=models.ForeignKey(default=None, to='bitcoin.BitcoinTransaction', null=True),
        ),
    ]
