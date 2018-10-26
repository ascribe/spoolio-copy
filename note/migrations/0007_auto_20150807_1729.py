# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Note = apps.get_model("note", "Note")
    for note in Note.objects.all():
        note.piece = note.edition.parent
        note.save()

class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0014_auto_20150703_1111'),
        ('note', '0006_publiceditionnote'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='piece',
            field=models.ForeignKey(related_name='note_at_piece', blank=True, to='piece.Piece', null=True),
        ),
        migrations.AlterField(
            model_name='note',
            name='edition',
            field=models.ForeignKey(related_name='note_at_edition', blank=True, to='piece.Edition', null=True),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
