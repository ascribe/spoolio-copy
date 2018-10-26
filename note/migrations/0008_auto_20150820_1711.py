# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    Note = apps.get_model("note", "Note")
    for note in Note.objects.filter(type__in=['Note', 'PublicEditionNote']):
        if note.type == 'Note':
            note.type = 'PrivateNote'
        elif note.type == 'PublicEditionNote':
            note.type = 'PublicNote'
        note.save()


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0007_auto_20150807_1729'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PublicEditionNote',
        ),
        migrations.CreateModel(
            name='PrivateNote',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('note.note',),
        ),
        migrations.CreateModel(
            name='PublicNote',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('note.privatenote',),
        ),
        migrations.RunPython(
            forwards_func,
        )
    ]
