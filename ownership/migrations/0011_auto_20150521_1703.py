# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0010_license'),
        ('piece', '0008_auto_20150521_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ownership',
            name='piece',
            field=models.ForeignKey(related_name='ownership_at_piece', to='piece.Edition'),
        ),
    ]
