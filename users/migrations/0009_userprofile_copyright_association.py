# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20150724_1508'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='copyright_association',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
