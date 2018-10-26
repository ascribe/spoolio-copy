# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0025_auto_20150908_1054'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contractagreement',
            old_name='datetime_sent',
            new_name='datetime_deleted',
        ),
    ]
