from django.db import models, migrations


def forwards_func(apps, schema_editor):
    ActionControl = apps.get_model("acl", "ActionControl")
    for acl in ActionControl.objects.filter(edition=None, acl_loan=False):
        if acl.piece.user_registered == acl.user:
            acl.acl_loan = True
            acl.save()

    OwnershipTransfer = apps.get_model("ownership", "OwnershipTransfer")
    for acl in ActionControl.objects.filter(acl_edit=True):
        if len(OwnershipTransfer.objects.filter(piece_id=acl.piece.id, type="OwnershipTransfer")) > 0:
            acl.acl_edit = False
            acl.save()

class Migration(migrations.Migration):

    dependencies = [
        ('acl', '0001_initial'),
        ('piece', '0018_auto_20150817_1445'),
        ('whitelabel', '0008_auto_20150817_2020')
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
