# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0003_whitelabelsettings_acl_view_editions'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_submit_to_prize',
            field=models.BooleanField(default=False),
        ),
    ]
