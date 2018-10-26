# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0003_auto_20150421_1344'),
    ]

    operations = [
        migrations.CreateModel(
            name='FederationWallet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.IntegerField()),
                ('confirmations', models.IntegerField()),
                ('vout', models.IntegerField()),
                ('txid', models.TextField()),
            ],
        ),
    ]
