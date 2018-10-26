# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0016_ownershippiece'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharePiece',
            fields=[
                ('ownership_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='ownership.Ownership')),
            ],
            bases=('ownership.share',),
        ),
    ]
