# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='piece',
            old_name='digital_work_model',
            new_name='digital_work',
        ),
        migrations.RenameField(
            model_name='piece',
            old_name='thumbnail_model',
            new_name='thumbnail',
        ),
        migrations.RenameField(
            model_name='piece',
            old_name='other_data_model',
            new_name='other_data',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='consignee_percentage',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='for_sale',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='sale_amount',
        ),
        migrations.RemoveField(
            model_name='piece',
            name='sale_currency',
        ),
    ]
