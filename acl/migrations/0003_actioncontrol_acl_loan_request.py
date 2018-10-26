# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from acl.test.util import APIUtilActionControl


def forwards_func(apps, schema_editor):
    ActionControl = apps.get_model("acl", "ActionControl")
    acl_util = APIUtilActionControl()

    for acl in ActionControl.objects.all():
        acl.acl_loan_request = True
        if acl_util.is_edition_acl_sharee(acl):
            acl.save()
        elif acl_util.is_piece_sharee(acl):
            acl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('acl', '0002_data_update_piece_loan_edit'),
    ]

    operations = [
        migrations.AddField(
            model_name='actioncontrol',
            name='acl_loan_request',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
