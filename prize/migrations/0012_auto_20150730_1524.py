# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0011_auto_20150729_1854'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ArtprizeJuryRole',
        ),
        migrations.DeleteModel(
            name='ArtprizeParticipantRole',
        ),
        migrations.DeleteModel(
            name='ArtprizeRole',
        ),
    ]
