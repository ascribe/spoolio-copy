# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0004_artprizejuryrole_artprizeparticipantrole_artprizerole'),
    ]

    operations = [
        migrations.RenameField(
            model_name='prize',
            old_name='promocodes',
            new_name='promocodes_str',
        ),
    ]
