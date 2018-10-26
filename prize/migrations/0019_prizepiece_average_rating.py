# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def get_average(obj):
    if len(obj) == 0:
        return None
    ratings = [float(r.note) for r in obj]
    return sum(ratings) / len(ratings)

def forwards_func(apps, schema_editor):
    PrizePiece = apps.get_model("prize", "PrizePiece")
    Rating = apps.get_model("prize", "Rating")
    for prizepiece in PrizePiece.objects.all():
        ratings = Rating.objects.filter(piece=prizepiece.piece, type="Rating")
        prizepiece.average_rating = get_average(ratings)
        prizepiece.save()


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0018_prizeuser_is_judge'),
    ]

    operations = [
        migrations.AddField(
            model_name='prizepiece',
            name='average_rating',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
