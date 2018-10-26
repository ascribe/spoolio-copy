# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('s3', '0005_auto_20150330_1449'),]

    database_operations = [
        migrations.AlterModelTable('ThumbnailModel', 'blobs_thumbnail'),
        migrations.AlterModelTable('DigitalWorkModel', 'blobs_digitalwork'),
        migrations.AlterModelTable('OtherDataModel', 'blobs_otherdata'),
        migrations.AlterModelTable('CoaFileModel', 'blobs_coafile'),
    ]

    state_operations = [
        migrations.DeleteModel('ThumbnailModel'),
        migrations.DeleteModel('DigitalWorkModel'),
        migrations.DeleteModel('OtherDataModel'),
        migrations.DeleteModel('CoaFileModel')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]