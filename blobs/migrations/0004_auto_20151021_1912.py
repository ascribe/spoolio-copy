# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def replace_thumbnail_sizes(apps, schema_editor):
    Thumbnail = apps.get_model('blobs', 'Thumbnail')

    for thumbnail in Thumbnail.objects.filter(thumbnail_sizes__isnull=False,
                                              thumbnail_file__contains='100x100'):
        thumbnail.thumbnail_file = thumbnail.thumbnail_file.replace('100x100', '300x300')
        thumbnail.save()


class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0003_thumbnail_thumbnail_sizes'),
    ]

    operations = [
        migrations.RunPython(replace_thumbnail_sizes),
    ]
