# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0027_auto_20150914_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='datetime_deleted',
            field=models.DateTimeField(default=None, null=True, blank=True),
        ),
    ]
