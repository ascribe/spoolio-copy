# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0006_auto_20150805_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_submit_to_cyland',
            field=models.BooleanField(default=False),
        ),
    ]
