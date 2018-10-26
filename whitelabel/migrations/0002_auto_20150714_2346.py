# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='whitelabelsettings',
            name='permissions',
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_coa',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_consign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_download',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_edit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_editions',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_loan',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_request_unconsign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_share',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_transfer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_unconsign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_unshare',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_view',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_withdraw_consign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_withdraw_transfer',
            field=models.BooleanField(default=False),
        ),
    ]
