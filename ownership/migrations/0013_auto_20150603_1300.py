# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
def forwards_func(apps, schema_editor):
    Ownership = apps.get_model('ownership', 'Ownership')
    for ownership in Ownership.objects.all():
        ownership.piece_id = ownership.edition.parent_id
        ownership.save()

class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0012_ownership_edition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ownership',
            name='piece',
            field=models.ForeignKey(related_name='ownership_at_piece', to='piece.Piece'),
        ),
        migrations.RunPython(
            forwards_func,
        )
    ]
