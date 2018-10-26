# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    Ownership = apps.get_model('ownership', 'Ownership')
    for ownership in Ownership.objects.all():
        ownership.edition_id = ownership.piece_id
        ownership.save()

class Migration(migrations.Migration):

    dependencies = [
        # ('piece', '0012_auto_20150522_1610'),
        ('ownership', '0011_auto_20150521_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownership',
            name='edition',
            field=models.ForeignKey(related_name='ownership_at_edition', blank=True, to='piece.Edition', null=True),
        ),
        migrations.RunPython(
            forwards_func,
        )
    ]
