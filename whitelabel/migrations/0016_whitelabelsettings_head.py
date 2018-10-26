# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0016_whitelabelsettings_acl_view_settings_copyright_association'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='head',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
