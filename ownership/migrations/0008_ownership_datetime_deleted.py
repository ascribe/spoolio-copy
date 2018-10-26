# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0007_ownershipmigration'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownership',
            name='datetime_deleted',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
