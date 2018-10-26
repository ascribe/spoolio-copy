# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0015_auto_20150817_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='other_datas',
            field=models.ForeignKey(related_name='otherdatas_at_piece', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='blobs.OtherData', null=True),
        ),
    ]
