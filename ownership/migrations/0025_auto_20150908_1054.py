# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0024_auto_20150825_1134'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contract',
            old_name='public',
            new_name='is_public',
        ),
    ]
