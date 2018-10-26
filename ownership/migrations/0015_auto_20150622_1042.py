# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0014_ownershipeditions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ownership',
            name='btc_tx',
            field=models.ForeignKey(related_name='ownership', blank=True, to='bitcoin.BitcoinTransaction', null=True),
        ),
    ]
