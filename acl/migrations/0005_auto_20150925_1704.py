# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

from ownership.models import Consignment
from acl.models import ActionControl
from piece.models import Edition


def forwards_func(apps, schema_editor):
    for e in Edition.objects.filter(consign_status=settings.PENDING_CONSIGN):
        try:
            o = Consignment.objects.get(edition=e)
            acl = ActionControl.objects.get(edition=e, user=o.new_owner)
            acl.acl_unconsign = False
            acl.save()
        except (models.ObjectDoesNotExist, Consignment.MultipleObjectsReturned):
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('acl', '0004_auto_20150826_1801'),
        ('ownership', '0028_contract_datetime_deleted')
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        )
    ]
