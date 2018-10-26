# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('note.note',),
        ),
        migrations.AlterField(
            model_name='note',
            name='piece',
            field=models.ForeignKey(related_name='note_at_piece', blank=True, to='piece.Piece', null=True),
            preserve_default=True,
        ),
    ]
