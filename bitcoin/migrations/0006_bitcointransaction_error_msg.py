# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitcoin', '0005_bitcointransaction_dependent_tx'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitcointransaction',
            name='error_msg',
            field=models.TextField(null=True, blank=True),
        ),
    ]
