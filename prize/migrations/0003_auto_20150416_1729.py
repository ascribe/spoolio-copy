# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0002_pieceatprize'),
        ('piece', '0004_auto_20150416_0931')
    ]

    operations = [
        migrations.AlterField(
            model_name='pieceatprize',
            name='piece',
            field=models.ForeignKey(blank=True, to='piece.Piece', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pieceatprize',
            name='prize',
            field=models.ForeignKey(to='prize.Prize', null=True),
            preserve_default=True,
        ),
    ]
