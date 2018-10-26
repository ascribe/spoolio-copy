# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20150427_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='datetime_response',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
