# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0022_auto_20150811_1041'),
    ]

    database_operations = [
        migrations.AlterModelTable('ActionControl', 'acl_actioncontrol')
    ]

    state_operations = [
        migrations.DeleteModel('ActionControl')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
