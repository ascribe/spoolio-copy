# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0003_delete_rating'),
        ('prize', '0005_auto_20150421_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('note.note',),
        ),
        migrations.RenameField(
            model_name='pieceatprize',
            old_name='extra_data',
            new_name='extra_data_str',
        ),
    ]
