# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0005_auto_20150805_1517'),
    ]

    operations = [
        migrations.RenameField(
            model_name='whitelabelsettings',
            old_name='acl_editions',
            new_name='acl_create_editions',
        ),
    ]
