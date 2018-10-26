# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0012_auto_20150522_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='bitcoin_path',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='num_editions',
            field=models.IntegerField(default=-1),
        ),
    ]
