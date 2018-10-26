# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Prize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=50)),
                ('rounds', models.IntegerField(null=True, blank=True)),
                ('active_round', models.IntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=False)),
                ('promocodes', models.CharField(default=b'{}', max_length=400)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
