# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0001_initial'),
    ]

    database_operations = [
        migrations.AlterModelTable('CoaFile', 'coa_coafile')
    ]

    state_operations = [
        migrations.DeleteModel('CoaFile')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]