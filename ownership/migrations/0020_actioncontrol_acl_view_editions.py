# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0019_actioncontrol'),
    ]

    operations = [
        migrations.AddField(
            model_name='actioncontrol',
            name='acl_view_editions',
            field=models.BooleanField(default=True),
        ),
    ]
