# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0027_auto_20150914_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='name',
            field=models.CharField(max_length=260),
        ),
    ]
