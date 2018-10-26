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
            name='Piece',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=180)),
                ('artist_name', models.CharField(max_length=120)),
                ('date_created', models.DateField()),
                ('edition_number', models.IntegerField()),
                ('num_editions', models.IntegerField()),
                ('datetime_registered', models.DateTimeField(auto_now_add=True)),
                ('extra_data_string', models.TextField(default=b'', blank=True)),
                ('bitcoin_ID', models.CharField(max_length=100)),
                ('bitcoin_ID_noPrefix', models.CharField(max_length=100)),
                ('thumbnail_model', models.IntegerField(null=True, blank=True)),
                ('digital_work_model', models.IntegerField(null=True, blank=True)),
                ('other_data_model', models.IntegerField(null=True, blank=True)),
                ('consignee_name', models.CharField(default=None, max_length=60, null=True)),
                ('consign_status', models.IntegerField(default=0, choices=[(0, b'-'), (1, b'Pending consign'), (2, b'Consigned'), (3, b'Pending unconsign')])),
                ('for_sale', models.BooleanField(default=False)),
                ('sale_amount', models.CharField(max_length=60, null=True)),
                ('sale_currency', models.CharField(max_length=3, null=True)),
                ('consignee_percentage', models.CharField(max_length=60, null=True)),
                ('owner', models.ForeignKey(related_name='piece_owned', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('pending_new_owner', models.ForeignKey(related_name='pending_piece_owned', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user_registered', models.ForeignKey(related_name='piece_registered', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
