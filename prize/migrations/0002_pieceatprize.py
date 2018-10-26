# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PieceAtPrize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('piece', models.IntegerField(null=True, blank=True)),
                ('prize', models.IntegerField(null=True, blank=True)),
                ('round', models.IntegerField(null=True, blank=True)),
                ('extra_data', models.TextField(default=b'', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
