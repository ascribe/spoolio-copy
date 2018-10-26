# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blobs', '0003_thumbnail_thumbnail_sizes'),
        ('ownership', '0023_auto_20150817_1133'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('blob', models.ForeignKey(to='blobs.OtherData')),
                ('issuer', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('name', models.CharField(max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('public', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ContractAgreement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_sent', models.DateTimeField(default=None, null=True, blank=True)),
                ('datetime_accepted', models.DateTimeField(default=None, null=True, blank=True)),
                ('datetime_rejected', models.DateTimeField(default=None, null=True, blank=True)),
                ('contract', models.ForeignKey(to='ownership.Contract')),
                ('signee', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('appendix', django.contrib.postgres.fields.hstore.HStoreField(null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='loandetail',
            name='contract_model',
            field=models.ForeignKey(blank=True, to='ownership.Contract', null=True),
        ),
    ]
