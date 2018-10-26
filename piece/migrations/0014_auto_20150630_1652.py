# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0013_auto_20150626_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='other_data',
            field=models.ForeignKey(related_name='otherdata_at_piece', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='blobs.OtherData', null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='thumbnail',
            field=models.ForeignKey(related_name='thumbnail_at_piece', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='blobs.Thumbnail', null=True),
        ),
    ]
