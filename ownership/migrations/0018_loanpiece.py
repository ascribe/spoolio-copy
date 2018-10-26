# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0017_sharepiece'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanPiece',
            fields=[
                ('ownership_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='ownership.Ownership')),
            ],
            bases=('ownership.loan',),
        ),
    ]
