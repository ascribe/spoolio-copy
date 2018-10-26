# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Piece = apps.get_model("piece", "Piece")
    default_license = apps.get_model("ownership", "License").objects.get(code="default")
    for piece in Piece.objects.all():
        first_piece = Piece.objects.filter(user_registered_id=piece.user_registered_id, title=piece.title,
                                           artist_name=piece.artist_name, date_created=piece.date_created).order_by("edition_number")[0]
        if not first_piece.id == piece.id:
            piece.delete()
        else:
            if piece.license_type is None:
                piece.license_type = default_license
                piece.save()

class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0008_auto_20150521_1538'),
        ('ownership', '0013_auto_20150603_1300'),
        ('prize', '0007_auto_20150521_1701'),
        ('note', '0004_auto_20150521_1603')
    ]

    operations = [
        migrations.RemoveField(
            model_name='piece',
            name='coa',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='consign_status',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='consignee_name',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='pending_new_owner',
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
