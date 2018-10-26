# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0017_piece_other_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='piece',
            name='other_datas',
        ),
        migrations.AlterField(
            model_name='piece',
            name='other_data',
            field=models.ManyToManyField(related_name='otherdata_at_piece', to='blobs.OtherData', blank=True),
        ),
    ]
