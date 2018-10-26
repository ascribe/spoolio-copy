# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0016_prizeuser_datetime_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizepiece',
            name='is_selected',
            field=models.BooleanField(default=False),
        ),
    ]
