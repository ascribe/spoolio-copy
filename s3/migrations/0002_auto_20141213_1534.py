# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='digitalworkmodel',
            name='digital_work_file',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='thumbnailmodel',
            name='thumbnail_file',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
    ]
