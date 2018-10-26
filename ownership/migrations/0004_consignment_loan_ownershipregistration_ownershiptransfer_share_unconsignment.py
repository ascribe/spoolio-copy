# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0003_auto_20150416_1517'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipRegistration',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
        migrations.CreateModel(
            name='OwnershipTransfer',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownershiptransfer',),
        ),
        migrations.CreateModel(
            name='Consignment',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownershiptransfer',),
        ),
        migrations.CreateModel(
            name='Share',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
        migrations.CreateModel(
            name='UnConsignment',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownershiptransfer',),
        ),
    ]
