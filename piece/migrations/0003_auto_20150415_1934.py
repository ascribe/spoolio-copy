# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0002_auto_20150415_1750'),
        ('blobs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='thumbnail',
            field=models.ForeignKey(related_name='thumbnail_at_piece', blank=True, to='blobs.Thumbnail', null=True),
            preserve_default=True,
        ),
    ]
