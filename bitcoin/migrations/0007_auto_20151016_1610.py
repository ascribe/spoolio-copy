# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from datetime import timedelta

from django.db import migrations
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password


def forwards_func(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Application = apps.get_model('oauth2_provider', 'Application')
    AccessToken = apps.get_model('oauth2_provider', 'AccessToken')

    # Create a user for blocktrail. Lets use the api key as a password
    password = make_password(settings.BLOCKTRAIL_API_KEY)
    blocktrail_user = User(username='blocktrail', email='blocktrail@ascribe.io',
                           is_staff=False, is_active=True, is_superuser=False,
                           date_joined=timezone.now(), password=password)
    blocktrail_user.save()

    # Create a app for the webhook
    app = Application(name='blocktrail', redirect_uris="", user_id=blocktrail_user.id,
                      client_type='confidential',
                      authorization_grant_type='password')
    app.save()

    # Create the token
    expires = timezone.now() + timedelta(days=10000)
    key_testnet = os.environ['BLOCKTRAIL_TOKEN']
    AccessToken.objects.create(user_id=blocktrail_user.id, token=key_testnet, application_id=app.id,
                               expires=expires, scope='write')


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0006_bitcointransaction_error_msg'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
