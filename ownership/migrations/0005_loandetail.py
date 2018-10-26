# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0004_consignment_loan_ownershipregistration_ownershiptransfer_share_unconsignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('loan', models.IntegerField(null=True, blank=True)),
                ('gallery', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
