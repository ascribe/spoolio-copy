# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('s3', '0006_auto_20150415_1858'),
    ]

    operations = [
        migrations.CreateModel(
            name='S3HttpRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('headers', django.contrib.postgres.fields.hstore.HStoreField(null=True)),
                ('verb', models.CharField(max_length=10)),
                ('path', models.TextField()),
                ('query_params', django.contrib.postgres.fields.hstore.HStoreField(null=True)),
                ('user', models.ForeignKey(related_name='httprequest_created', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
