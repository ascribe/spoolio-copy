# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0010_whitelabelsettings_acl_loan_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='whitelabelsettings',
            name='acl_accepted',
            field=models.BooleanField(default=False),
        ),
    ]
