# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0005_auto_20150604_1603'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicEditionNote',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('note.note',),
        ),
    ]
