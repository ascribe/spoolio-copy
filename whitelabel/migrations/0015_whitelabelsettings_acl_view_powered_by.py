# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0014_whitelabelsettings_acl_create_piece'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_powered_by',
            field=models.BooleanField(default=False),
        ),
    ]
