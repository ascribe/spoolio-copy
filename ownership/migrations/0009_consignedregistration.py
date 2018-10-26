# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0008_ownership_datetime_deleted'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsignedRegistration',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ownership.ownership',),
        ),
    ]
