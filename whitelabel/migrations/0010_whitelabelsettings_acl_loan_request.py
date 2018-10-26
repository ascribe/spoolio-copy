# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0009_whitelabelsettings_acl_submitted'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_loan_request',
            field=models.BooleanField(default=False),
        ),
    ]
