# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    PrizePiece = apps.get_model("prize", "PrizePiece")
    Rating = apps.get_model("prize", "Rating")
    for prizepiece in PrizePiece.objects.all():
        ratings = Rating.objects.filter(piece=prizepiece.piece, type="Rating")
        prizepiece.num_ratings = len(ratings) if ratings else None
        prizepiece.save()


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0019_prizepiece_average_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizepiece',
            name='num_ratings',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
