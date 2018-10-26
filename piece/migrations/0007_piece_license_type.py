# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0010_license'),
        ('piece', '0006_piece_datetime_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='license_type',
            field=models.ForeignKey(related_name='license_at_piece', blank=True, to='ownership.License', null=True),
        ),
    ]
