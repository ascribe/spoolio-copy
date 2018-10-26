# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0014_auto_20150703_1111'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('prize', '0008_prizeuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrizePiece',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('piece', models.ForeignKey(to='piece.Piece')),
                ('prize', models.ForeignKey(to='prize.Prize')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
