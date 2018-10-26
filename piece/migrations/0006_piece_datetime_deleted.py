# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0005_piece_coa'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='datetime_deleted',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
