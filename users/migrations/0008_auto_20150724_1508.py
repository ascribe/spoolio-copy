# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_usertokenrole_uservalidateemailrole'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='hash_locally',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='language',
            field=models.CharField(default=b'en', max_length=10),
        ),
    ]
