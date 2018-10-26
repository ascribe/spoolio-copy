# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0007_auto_20151016_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='federationwallet',
            name='type',
            field=models.CharField(default=b'', max_length=100),
        ),
    ]
