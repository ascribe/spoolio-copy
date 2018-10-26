# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0012_auto_20150730_1524'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prize',
            name='promocodes_str',
        ),
    ]
