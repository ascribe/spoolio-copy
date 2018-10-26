# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0010_prizepiece_extra_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizeuser',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prizeuser',
            name='is_jury',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prizeuser',
            name='round',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='prizeuser',
            unique_together=set([('prize', 'user', 'is_jury', 'round')]),
        ),
    ]
