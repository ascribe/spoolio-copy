# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0006_auto_20150416_1842'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipMigration',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
    ]
