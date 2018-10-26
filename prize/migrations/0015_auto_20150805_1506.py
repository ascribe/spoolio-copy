# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0014_auto_20150804_1155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prize',
            name='active_round',
            field=models.IntegerField(default=1, null=True, blank=True),
        ),
    ]
