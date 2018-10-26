# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0009_auto_20150521_1706'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='piece',
            name='bitcoin_id',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='edition_number',
        ),
        migrations.AlterField(
            model_name='edition',
            name='parent',
            field=models.ForeignKey(related_name='piece_at_edition', to='piece.Piece'),
        ),
    ]
