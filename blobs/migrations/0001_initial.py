# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import blobs.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('s3', '0006_auto_20150415_1858')
    ]

    state_operations = [
        migrations.CreateModel(
            name='CoaFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coa_file', models.CharField(max_length=2000)),
                ('piece', models.IntegerField(null=True, blank=True)),
                ('user', models.ForeignKey(related_name='coa_files_at_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model, blobs.models.File),
        ),
        migrations.CreateModel(
            name='DigitalWork',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('digital_work_file', models.CharField(max_length=2000)),
                ('digital_work_hash', models.CharField(max_length=2000)),
                ('user', models.ForeignKey(related_name='digital_works_at_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model, blobs.models.File),
        ),
        migrations.CreateModel(
            name='OtherData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('other_data_file', models.CharField(max_length=2000)),
                ('user', models.ForeignKey(related_name='other_datas_at_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model, blobs.models.File),
        ),
        migrations.CreateModel(
            name='Thumbnail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('thumbnail_file', models.CharField(max_length=2000)),
                ('user', models.ForeignKey(related_name='thumbnails_at_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model, blobs.models.File),
        ),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]