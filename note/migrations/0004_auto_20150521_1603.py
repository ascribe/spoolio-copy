# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

    dependencies = [
        ('note', '0003_delete_rating'),
        ('piece', '0008_auto_20150521_1538')
    ]

    operations = [
        migrations.AlterField(
            model_name='note',
            name='piece',
            field=models.ForeignKey(related_name='note_at_piece', blank=True, to='piece.Edition', null=True),
        ),
    ]
