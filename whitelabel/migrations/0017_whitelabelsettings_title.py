# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0016_whitelabelsettings_head'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='title',
            field=models.CharField(max_length=20, blank=True),
        ),
    ]
