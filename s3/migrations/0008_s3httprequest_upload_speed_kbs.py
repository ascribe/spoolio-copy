# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('s3', '0007_s3httprequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='s3httprequest',
            name='upload_speed_kbs',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
