# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNeedsToRegisterRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.role',),
        ),
    ]
