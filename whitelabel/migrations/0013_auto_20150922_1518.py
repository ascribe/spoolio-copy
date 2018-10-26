# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0012_auto_20150922_1443'),
    ]

    operations = [
        migrations.RenameField(
            model_name='whitelabelsettings',
            old_name='acl_accepted',
            new_name='acl_wallet_accepted',
        ),
        migrations.RenameField(
            model_name='whitelabelsettings',
            old_name='acl_submit',
            new_name='acl_wallet_submit',
        ),
        migrations.RenameField(
            model_name='whitelabelsettings',
            old_name='acl_submitted',
            new_name='acl_wallet_submitted',
        ),
    ]
