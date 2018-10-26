# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0009_prizepiece'),
    ]

    operations = [
        migrations.AddField(
            model_name='prize',
            name='num_submissions',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
