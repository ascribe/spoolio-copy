# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0010_auto_20150521_1741'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='piece',
            name='bitcoin_ID_noPrefix',
        ),
    ]
