# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0026_auto_20150909_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownership',
            name='contract_agreement',
            field=models.ForeignKey(related_name='ownership_at_contractagreement', blank=True, to='ownership.ContractAgreement', null=True),
        ),
    ]
