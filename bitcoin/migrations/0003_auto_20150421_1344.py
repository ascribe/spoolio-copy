# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0002_bitcoinwallet'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bitcointransaction',
            old_name='inputs',
            new_name='inputs_str',
        ),
        migrations.RenameField(
            model_name='bitcointransaction',
            old_name='outputs',
            new_name='outputs_str',
        ),
        migrations.RenameField(
            model_name='bitcointransaction',
            old_name='service',
            new_name='service_str',
        ),
    ]
