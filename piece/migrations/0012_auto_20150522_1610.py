# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0011_remove_piece_bitcoin_id_noprefix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='user_registered',
            field=models.ForeignKey(related_name='piece_registered', to=settings.AUTH_USER_MODEL),
        ),
    ]
