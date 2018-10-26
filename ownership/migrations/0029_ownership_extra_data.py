# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0028_contract_datetime_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownership',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(null=True),
        ),
    ]
