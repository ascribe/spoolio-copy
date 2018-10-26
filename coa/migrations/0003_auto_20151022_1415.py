# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    """
    Set coa to None so that from now on all the coas need to be re-created with
    the new redesign.
    """
    Edition = apps.get_model('piece', 'Edition')
    for edition in Edition.objects.all():
        edition.coa = None
        edition.save()


class Migration(migrations.Migration):

    dependencies = [
        ('coa', '0002_auto_20150604_1053'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
