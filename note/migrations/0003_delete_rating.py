# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0002_auto_20150416_1340'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Rating',
        ),
    ]
