# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0017_prizepiece_is_selected'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizeuser',
            name='is_judge',
            field=models.BooleanField(default=False),
        ),
    ]
