# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0014_auto_20150630_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='license_type',
            field=models.ForeignKey(related_name='license_at_piece', blank=True, to='ownership.License', null=True),
        ),
    ]
