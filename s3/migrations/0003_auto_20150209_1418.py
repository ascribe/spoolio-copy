# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('s3', '0002_auto_20141213_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitalworkmodel',
            name='user',
            field=models.ForeignKey(related_name='digital_work_at_user', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='otherdatamodel',
            name='user',
            field=models.ForeignKey(related_name='other_data_at_user', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='thumbnailmodel',
            name='user',
            field=models.ForeignKey(related_name='thumbnail_at_user', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
