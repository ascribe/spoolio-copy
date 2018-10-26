# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0013_auto_20150603_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipEditions',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
    ]
