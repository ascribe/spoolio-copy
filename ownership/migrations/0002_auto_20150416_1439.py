# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0001_initial'),
        ('piece', '0004_auto_20150416_0931')
    ]

    operations = [
        migrations.AlterField(
            model_name='ownership',
            name='piece',
            field=models.ForeignKey(related_name='ownership_at_piece', blank=True, to='piece.Piece', null=True),
            preserve_default=True,
        ),
    ]
