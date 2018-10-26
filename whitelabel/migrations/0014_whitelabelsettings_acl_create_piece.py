# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0013_auto_20150922_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_create_piece',
            field=models.BooleanField(default=True),
        ),
    ]
