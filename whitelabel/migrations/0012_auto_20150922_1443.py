# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0011_whitelabelsettings_acl_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_create_contractagreement',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_edit_private_contract',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_edit_public_contract',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_intercom',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_update_private_contract',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_update_public_contract',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_account',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_account_hash',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_api',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_bitcoin',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view_settings_contract',
            field=models.BooleanField(default=True),
        ),
    ]
