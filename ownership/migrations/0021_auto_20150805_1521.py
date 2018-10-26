# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    ActionControl = apps.get_model("ownership", "ActionControl")
    for acl in ActionControl.objects.all():
        if acl.edition is None:
            if acl.piece.num_editions > -1:
                acl.acl_create_editions = False
            else:
                acl.acl_create_editions = True
        elif acl.edition is not None:
            acl.acl_create_editions = False
        acl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0020_actioncontrol_acl_view_editions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='actioncontrol',
            old_name='acl_editions',
            new_name='acl_create_editions',
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
