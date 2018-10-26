# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('s3', '0003_auto_20150209_1418'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoaFileModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coa_file', models.CharField(max_length=200)),
                ('piece', models.IntegerField(null=True, blank=True)),
                ('user', models.ForeignKey(related_name='coa_file_at_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
