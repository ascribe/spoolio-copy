# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coa', '0001_initial'),
        ('piece', '0004_auto_20150416_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='coa',
            field=models.ForeignKey(related_name='coafile_at_piece', blank=True, to='coa.CoaFile', null=True),
            preserve_default=True,
        ),
    ]
