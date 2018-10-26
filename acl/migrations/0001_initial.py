# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0023_auto_20150817_1133'),
        ('piece', '0014_auto_20150703_1111'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    state_operations = [
        migrations.CreateModel(
            name='ActionControl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acl_view', models.BooleanField(default=False)),
                ('acl_edit', models.BooleanField(default=False)),
                ('acl_download', models.BooleanField(default=False)),
                ('acl_delete', models.BooleanField(default=False)),
                ('acl_create_editions', models.BooleanField(default=False)),
                ('acl_view_editions', models.BooleanField(default=True)),
                ('acl_share', models.BooleanField(default=False)),
                ('acl_unshare', models.BooleanField(default=False)),
                ('acl_transfer', models.BooleanField(default=False)),
                ('acl_withdraw_transfer', models.BooleanField(default=False)),
                ('acl_consign', models.BooleanField(default=False)),
                ('acl_withdraw_consign', models.BooleanField(default=False)),
                ('acl_unconsign', models.BooleanField(default=False)),
                ('acl_request_unconsign', models.BooleanField(default=False)),
                ('acl_loan', models.BooleanField(default=False)),
                ('acl_coa', models.BooleanField(default=False)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('edition', models.ForeignKey(related_name='acl_at_edition', blank=True, to='piece.Edition', null=True)),
                ('piece', models.ForeignKey(related_name='acl_at_piece', blank=True, to='piece.Piece', null=True)),
                ('user', models.ForeignKey(related_name='acl_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
