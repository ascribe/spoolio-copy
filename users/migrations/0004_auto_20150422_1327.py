# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userneedstoregisterrole'),
    ]

    operations = [
        migrations.RenameField(
            model_name='role',
            old_name='role',
            new_name='role_str',
        ),
    ]
