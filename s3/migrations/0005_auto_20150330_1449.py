# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0004_coafilemodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coafilemodel',
            name='coa_file',
            field=models.CharField(max_length=2000),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='digitalworkmodel',
            name='digital_work_file',
            field=models.CharField(max_length=2000),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='digitalworkmodel',
            name='digital_work_hash',
            field=models.CharField(max_length=2000),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='otherdatamodel',
            name='other_data_file',
            field=models.CharField(max_length=2000),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='thumbnailmodel',
            name='thumbnail_file',
            field=models.CharField(max_length=2000),
            preserve_default=True,
        ),
    ]
