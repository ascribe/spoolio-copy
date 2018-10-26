# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Edition = apps.get_model("piece", "Edition")
    Role = apps.get_model("users", "Role")
    OwnershipTransfer = apps.get_model("ownership", "OwnershipTransfer")
    ActionControl = apps.get_model("acl", "ActionControl")
    for ed in Edition.objects.filter(pending_new_owner__isnull=False):
        try:
            Role.objects.get(user=ed.pending_new_owner, type='UserNeedsToRegisterRole')
        except Role.DoesNotExist:
            try:
                ownership_transfer = OwnershipTransfer.objects.get(edition=ed,
                                                                   new_owner=ed.pending_new_owner,
                                                                   type='OwnershipTransfer')

                ownership_transfer.edition.pending_new_owner = None
                ownership_transfer.edition.owner = ownership_transfer.new_owner
                ownership_transfer.edition.save()
                ownership_transfer.save()
                acl = ActionControl.objects.get(user=ownership_transfer.prev_owner,
                                                piece=ownership_transfer.edition.parent,
                                                edition=ownership_transfer.edition)
                acl.acl_withdraw_transfer = False
                acl.acl_unshare = True
                acl.save()
            except OwnershipTransfer.MultipleObjectsReturned:
                print 'multiple'
                print ed.id
            except OwnershipTransfer.DoesNotExist:
                print 'none'
                print ed.id


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0009_userprofile_copyright_association'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
