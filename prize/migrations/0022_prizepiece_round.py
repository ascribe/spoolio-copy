# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    PrizePiece = apps.get_model("prize", "PrizePiece")
    for prize_piece in PrizePiece.objects.all():
        if prize_piece.is_selected:
            prize_piece.round += 1
            prize_piece.is_selected = False
            prize_piece.save()


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0021_auto_20151210_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizepiece',
            name='round',
            field=models.IntegerField(default=1, null=True, blank=True),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
