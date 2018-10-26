# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_func(apps, schema_editor):
    Prize = apps.get_model("prize", "Prize")
    PrizePiece = apps.get_model("prize", "PrizePiece")
    ActionControl = apps.get_model("acl", "ActionControl")

    try:
        prize = Prize.objects.get(name='sluice')
    except Prize.DoesNotExist:
        print 'prize doesnt exist'
        pass
    else:
        for prize_piece in PrizePiece.objects.filter(prize=prize):
            acl = ActionControl.objects.get(piece=prize_piece.piece, user=prize_piece.user, edition=None)
            acl.acl_delete = True
            acl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('prize', '0020_prizepiece_num_ratings'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
