# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0004_auto_20150521_1603'),
    ]

    operations = [
        migrations.RenameField(
            model_name='note',
            old_name='piece',
            new_name='edition',
        ),
    ]
