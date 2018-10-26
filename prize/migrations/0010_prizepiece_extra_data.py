# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0010_prize_num_submissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizepiece',
            name='extra_data',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
