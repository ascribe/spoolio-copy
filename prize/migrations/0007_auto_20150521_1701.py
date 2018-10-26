# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0006_auto_20150423_1100'),
        ('piece', '0008_auto_20150521_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pieceatprize',
            name='piece',
            field=models.ForeignKey(to='piece.Edition'),
        ),
        migrations.AlterField(
            model_name='pieceatprize',
            name='prize',
            field=models.ForeignKey(to='prize.Prize'),
        ),
    ]
