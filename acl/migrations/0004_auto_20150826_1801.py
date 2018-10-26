# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def forwards_func(apps, schema_editor):
    ActionControl = apps.get_model("acl", "ActionControl")
    Edition = apps.get_model("piece", "Edition")

    for edition in Edition.objects.filter(datetime_deleted__isnull=True,
                                          consignee_id__isnull=False,
                                          consign_status__in=[settings.CONSIGNED, settings.PENDING_CONSIGN]):

        if edition.consign_status == settings.PENDING_CONSIGN:
            acl = ActionControl.objects.get(user=edition.consignee, edition=edition)
            acl.acl_loan = False
            acl.acl_transfer = False
            acl.acl_coa = False
            acl.save()
        elif edition.consign_status == settings.CONSIGNED:
            acl = ActionControl.objects.get(user=edition.consignee, edition=edition)
            acl.loan = True
            acl.acl_transfer = True
            acl.save()




class Migration(migrations.Migration):

    dependencies = [
        ('acl', '0003_actioncontrol_acl_loan_request'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
