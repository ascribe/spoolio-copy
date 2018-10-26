# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL)
    ]

    operations = [
        migrations.CreateModel(
            name='BitcoinTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('service', models.CharField(max_length=50, null=True, blank=True)),
                ('from_address', models.CharField(max_length=100)),
                ('inputs', models.TextField(null=True, blank=True)),
                ('outputs', models.TextField(null=True, blank=True)),
                ('mining_fee', models.IntegerField(null=True, blank=True)),
                ('tx', models.TextField(max_length=100, null=True, blank=True)),
                ('block_height', models.IntegerField(null=True, blank=True)),
                ('status', models.IntegerField(default=0, null=True, blank=True, choices=[(0, b'Pending'), (1, b'Unconfirmed'), (2, b'Confirmed'), (3, b'Rejected')])),
                ('spoolverb', models.CharField(max_length=40, null=True, blank=True)),
                ('user', models.ForeignKey(related_name='tx_created', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
