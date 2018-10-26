# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def change_whitelabel_settings(apps, schema_editor):
    WhitelabelSettings = apps.get_model('whitelabel', 'WhitelabelSettings')
    settings_23vivi = WhitelabelSettings.objects.get(subdomain='23vivi')
    settings_polline = WhitelabelSettings.objects.get(subdomain='polline')

    settings_23vivi.acl_view_powered_by = False
    settings_polline.name = 'Polline'

    settings_23vivi.save()
    settings_polline.save()


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel', '0017_whitelabelsettings_title'),
    ]

    operations = [
        migrations.RunPython(change_whitelabel_settings),
    ]
