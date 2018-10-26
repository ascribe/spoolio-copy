# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userneedstoregisterrole'),
        ('prize', '0003_auto_20150416_1729'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArtprizeRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.role',),
        ),
        migrations.CreateModel(
            name='ArtprizeParticipantRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('prize.artprizerole',),
        ),
        migrations.CreateModel(
            name='ArtprizeJuryRole',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('prize.artprizerole',),
        ),
    ]
