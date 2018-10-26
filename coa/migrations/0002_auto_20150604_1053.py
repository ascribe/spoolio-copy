# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coa', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coafile',
            old_name='piece',
            new_name='edition',
        ),
    ]
