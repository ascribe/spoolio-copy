# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ownership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('piece', models.IntegerField(null=True, blank=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('datetime_response', models.DateTimeField(null=True, blank=True)),
                ('status', models.IntegerField(null=True, blank=True)),
                ('datetime_from', models.DateTimeField(null=True, blank=True)),
                ('datetime_to', models.DateTimeField(null=True, blank=True)),
                ('btc_tx', models.IntegerField(null=True, blank=True)),
                ('prev_btc_address', models.CharField(max_length=100, null=True, blank=True)),
                ('new_btc_address', models.CharField(max_length=100, null=True, blank=True)),
                ('type', models.CharField(max_length=30, null=True, blank=True)),
                ('ciphertext_password', models.CharField(max_length=100, null=True, blank=True)),
                ('new_owner', models.ForeignKey(related_name='ownership_to', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('prev_owner', models.ForeignKey(related_name='ownership_from', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
