# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0015_auto_20150805_1506'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizeuser',
            name='datetime_deleted',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
