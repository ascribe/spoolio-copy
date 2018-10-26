# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0004_whitelabelsettings_acl_submit_to_prize'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whitelabelsettings',
            name='acl_view_editions',
            field=models.BooleanField(default=True),
        ),
    ]
