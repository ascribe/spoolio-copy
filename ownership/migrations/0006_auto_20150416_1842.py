# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0001_initial'),
        ('ownership', '0005_loandetail'),
    ]

    operations = [
        migrations.AddField(
            model_name='loandetail',
            name='contract_model',
            field=models.ForeignKey(related_name='loan_contract', blank=True, to='blobs.OtherData', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='loandetail',
            name='loan',
            field=models.ForeignKey(related_name='detail_at_loan', blank=True, to='ownership.Loan', null=True),
            preserve_default=True,
        ),
    ]
