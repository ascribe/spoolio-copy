# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0015_auto_20150622_1042'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipPiece',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
    ]
