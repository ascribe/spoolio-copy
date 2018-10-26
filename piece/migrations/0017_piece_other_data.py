# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
def forwards_func(apps, schema_editor):
    Piece = apps.get_model('piece', 'Piece')
    for piece in Piece.objects.all():
        if piece.other_datas:
            piece.other_data.add(piece.other_datas)

class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0003_thumbnail_thumbnail_sizes'),
        ('piece', '0016_auto_20150817_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='other_data',
            field=models.ManyToManyField(related_name='otherdata_at_piece', null=True, to='blobs.OtherData', blank=True),
        ),
        migrations.RunPython(
            forwards_func,
        )
    ]
