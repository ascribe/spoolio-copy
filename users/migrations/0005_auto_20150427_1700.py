# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20150422_1327'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRequestResetPasswordRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.role',),
        ),
        migrations.CreateModel(
            name='UserResetPasswordRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.role',),
        ),
        migrations.AlterField(
            model_name='role',
            name='role_str',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='role',
            name='type',
            field=models.CharField(max_length=120, null=True, blank=True),
            preserve_default=True,
        ),
    ]
