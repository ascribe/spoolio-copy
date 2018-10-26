# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0015_whitelabelsettings_acl_view_powered_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_copyright_association',
            field=models.BooleanField(default=False),
        ),
    ]
