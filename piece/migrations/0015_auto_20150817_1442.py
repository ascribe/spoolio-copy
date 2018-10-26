# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0014_auto_20150703_1111'),
    ]

    operations = [
        migrations.RenameField(
            model_name='piece',
            old_name='other_data',
            new_name='other_datas',
        ),
    ]
