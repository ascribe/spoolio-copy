# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0003_auto_20150415_1934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='digital_work',
            field=models.ForeignKey(related_name='digitalwork_at_piece', blank=True, to='blobs.DigitalWork', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='piece',
            name='other_data',
            field=models.ForeignKey(related_name='otherdata_at_piece', blank=True, to='blobs.OtherData', null=True),
            preserve_default=True,
        ),
    ]
