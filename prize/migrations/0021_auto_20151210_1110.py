# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0017_whitelabelsettings_title'),
        ('prize', '0020_auto_20150825_1441'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prize',
            name='name',
        ),
        migrations.AddField(
            model_name='prize',
            name='whitelabel_settings',
            field=models.ForeignKey(to='whitelabel.WhitelabelSettings', null=True),
        ),
    ]
