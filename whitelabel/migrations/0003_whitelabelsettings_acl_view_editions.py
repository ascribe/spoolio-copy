# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0002_auto_20150714_2346'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_editions',
            field=models.BooleanField(default=False),
        ),
    ]
