# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.postgres.operations import HStoreExtension

from django.db import models, migrations
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0002_auto_20150423_0906'),
    ]

    operations = [
        migrations.AddField(
            model_name='thumbnail',
            name='thumbnail_sizes',
            field=django.contrib.postgres.fields.hstore.HStoreField(null=True),
        ),
    ]
