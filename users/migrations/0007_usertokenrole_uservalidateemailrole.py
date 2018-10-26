# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_role_datetime_response'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTokenRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.role',),
        ),
        migrations.CreateModel(
            name='UserValidateEmailRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.usertokenrole',),
        ),
    ]
