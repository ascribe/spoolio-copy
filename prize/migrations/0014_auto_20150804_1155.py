# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0013_remove_prize_promocodes_str'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prize',
            name='rounds',
            field=models.IntegerField(default=1),
        ),
    ]
