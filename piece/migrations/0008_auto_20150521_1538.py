# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Piece = apps.get_model("piece", "Piece")
    User = apps.get_model("auth", "User")
    Edition = apps.get_model("piece", "Edition")
    for piece in Piece.objects.all():
        try:
            consignee = User.objects.get(email=piece.consignee_name) if not piece.consignee_name in [None, ''] else None
        except:
            consignee = None
        parent = Piece.objects.filter(user_registered_id=piece.user_registered_id, title=piece.title,
                                      artist_name=piece.artist_name, date_created=piece.date_created).order_by("edition_number")[0]
        Edition(id=piece.id,
                edition_number=piece.edition_number,
                bitcoin_path=piece.bitcoin_id,
                consign_status=piece.consign_status,
                coa_id=piece.coa.id if piece.coa else None,
                owner_id=piece.owner.id,
                pending_new_owner_id=piece.pending_new_owner_id,
                datetime_deleted=piece.datetime_deleted,
                consignee_id=consignee.id if consignee else None,
                parent_id=parent.id).save()
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT setval('piece_edition_id_seq', (SELECT MAX(id) FROM piece_edition));")
    cursor.close()

class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0010_license'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coa', '0001_initial'),
        ('piece', '0007_piece_license_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Edition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('edition_number', models.IntegerField()),
                ('bitcoin_path', models.CharField(max_length=100)),
                ('datetime_deleted', models.DateTimeField(null=True, blank=True)),
                ('consign_status', models.IntegerField(default=0, choices=[(0, b'-'), (1, b'Pending consign'), (2, b'Consigned'), (3, b'Pending unconsign')])),
                ('coa', models.ForeignKey(related_name='coafile_at_piece', blank=True, to='coa.CoaFile', null=True)),
                ('consignee', models.ForeignKey(related_name='pending_piece_consigned', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('owner', models.ForeignKey(related_name='piece_owned', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='piece',
            old_name='bitcoin_ID',
            new_name='bitcoin_id',
        ),
        migrations.AlterField(
            model_name='piece',
            name='coa',
            field=models.ForeignKey(related_name='coafile_at_piece_', blank=True, to='coa.CoaFile', null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='digital_work',
            field=models.ForeignKey(related_name='digitalwork_at_piece', to='blobs.DigitalWork'),
        ),
        migrations.AlterField(
            model_name='piece',
            name='license_type',
            field=models.ForeignKey(related_name='license_at_piece_', blank=True, to='ownership.License', null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='owner',
            field=models.ForeignKey(related_name='piece_owned_', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='pending_new_owner',
            field=models.ForeignKey(related_name='pending_piece_owned_', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='piece',
            name='user_registered',
            field=models.ForeignKey(related_name='piece_registered_', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='edition',
            name='parent',
            field=models.ForeignKey(related_name='piece_at_edition', blank=True, to='piece.Piece', null=True),
        ),
        migrations.AddField(
            model_name='edition',
            name='pending_new_owner',
            field=models.ForeignKey(related_name='pending_piece_owned', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
