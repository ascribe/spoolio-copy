# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0008_auto_20150817_2020'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_submitted',
            field=models.BooleanField(default=False),
        ),
    ]
