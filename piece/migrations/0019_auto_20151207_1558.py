# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0018_auto_20150817_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edition',
            name='coa',
            field=models.ForeignKey(related_name='coafile_at_piece', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='coa.CoaFile', null=True),
        ),
        migrations.AlterField(
            model_name='edition',
            name='consignee',
            field=models.ForeignKey(related_name='pending_piece_consigned', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='edition',
            name='owner',
            field=models.ForeignKey(related_name='piece_owned', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='edition',
            name='pending_new_owner',
            field=models.ForeignKey(related_name='pending_piece_owned', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='license_type',
            field=models.ForeignKey(related_name='license_at_piece', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='ownership.License', null=True),
        ),
    ]
