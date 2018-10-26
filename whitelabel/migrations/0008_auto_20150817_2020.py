# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0007_whitelabelsettings_acl_submit_to_cyland'),
    ]

    operations = [
        migrations.RenameField(
            model_name='whitelabelsettings',
            old_name='acl_submit_to_cyland',
            new_name='acl_submit',
        ),
        migrations.RemoveField(
            model_name='whitelabelsettings',
            name='acl_submit_to_prize',
        ),
    ]
