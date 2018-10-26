# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, connection
from django.conf import settings

SQL_EDITIONS_BODY = """
        FROM
            ownership_ownership
            RIGHT OUTER JOIN piece_edition
                ON (ownership_ownership.edition_id = piece_edition.id)

        WHERE
            ((
                (ownership_ownership.new_owner_id = %s) AND
                (ownership_ownership.datetime_deleted ISNULL) AND
                -- status is not 0
                (ownership_ownership.status ISNULL OR ownership_ownership.status > 0) AND
                (   -- accepted and within from-to range
                    (
                    -- commented this because piece needs to be available for install
                    -- ownership_ownership.datetime_from <= NOW() AND
                      ownership_ownership.datetime_to > NOW() AND
                      ownership_ownership.status > 0) OR
                    -- pending (status is null) and not expired
                    (ownership_ownership.status ISNULL AND
                     ownership_ownership.datetime_to > NOW()) OR
                    -- no range
                    (ownership_ownership.datetime_from ISNULL AND
                     ownership_ownership.datetime_to ISNULL)
                )
            )
            OR
                piece_edition.owner_id = %s OR
                piece_edition.pending_new_owner_id = %s OR
                piece_edition.consignee_id = %s
            )
            AND
            piece_edition.datetime_deleted ISNULL
    """

def get_ids_editions(user_id):
    SQL = \
    """
        SELECT DISTINCT
            piece_edition.id
    """ + SQL_EDITIONS_BODY
    cursor = _run_sql(SQL, user_id)
    l = cursor.fetchall()
    cursor.close()
    return [rows[0] for rows in l]

def _run_sql(SQL, user_id):
    cursor = connection.cursor()
    cursor.execute(SQL , [user_id, user_id, user_id, user_id])
    return cursor

def most_recent_transfer(apps, edition):
    OwnershipTransfer = apps.get_model("ownership", "OwnershipTransfer")
    # could also calculate this via the chain of bitcoin addresses
    # (and that could be done independently of the DB, using the blockchain)
    # TODO: do we need the exclude? A: yes for btc_owner_address, but might miss some transfers
    transfers = OwnershipTransfer.objects.filter(edition_id=edition.id).exclude(btc_tx=None).order_by("datetime")
    n_transfers = len(transfers)
    if n_transfers > 0:
        return transfers[n_transfers - 1]
    else:
        return None

def acl_piece_user(apps, piece, user, Edition):
    acl = []
    SharePiece = apps.get_model("ownership", "SharePiece")
    """ edit additional details """
    editions = Edition.objects.filter(parent_id=piece.id).order_by("edition_number")
    if (user == piece.user_registered) \
            and (editions < 1 or \
            (all((most_recent_transfer(apps, e) is None) for e in editions))):
        acl += ['edit']

    if (piece.num_editions < 1) and (user == piece.user_registered):
        acl += ['editions']

    """ share, download, view """
    acl += ["share", "download", "view"]

    """ unshare """
    if len(SharePiece.objects.filter(new_owner=user.id, piece=piece.id, datetime_deleted=None)):
        acl += ["unshare"]
    return acl

def acl_edition_user(apps, edition, user, Edition):
    acl = []
    Share = apps.get_model("ownership", "Share")
    """ edit additional details """
    if all(most_recent_transfer(apps, s) is None for s in Edition.objects.filter(parent=edition.parent.id)) \
            and (user == edition.owner):
        acl += ['edit']

    """ consign """
    if (edition.owner.username == user.username
        and edition.pending_new_owner is None
        and edition.consignee is None):
        acl += ["consign"]

    if (edition.owner == user and edition.consign_status == settings.PENDING_CONSIGN):
        acl += ["withdraw_consign"]

    """ unconsign """
    if (edition.consignee == user and edition.consign_status == settings.CONSIGNED):
        acl += ["unconsign"]

    if (edition.owner == user and edition.consign_status == settings.CONSIGNED):
        acl += ["request_unconsign"]

    """ transfer """
    if "consign" in acl \
            or (edition.consignee == user
                and edition.consign_status in [settings.CONSIGNED, settings.PENDING_UNCONSIGN]):
        acl += ["transfer"]

    if (edition.owner.username == user.username
        and edition.pending_new_owner is not None):
        acl += ["withdraw_transfer"]

    """ loan """
    if "transfer" in acl:
        acl += ["loan"]

    """ share, download, view """
    acl += ["share", "download", "view"]

    """ unshare """
    if len(Share.objects.filter(new_owner=user.id, edition_id=edition.id, datetime_deleted=None)):
        acl += ["unshare"]

    """ delete """
    if (edition.owner.username == user.username
        and edition.pending_new_owner is None):
        acl += ["delete"]

    """ coa """
    if (edition.owner.username == user.username
        and edition.pending_new_owner is None):
        acl += ["coa"]
    return acl


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Piece = apps.get_model("piece", "Piece")
    Edition = apps.get_model("piece", "Edition")
    ActionControl = apps.get_model("ownership", "ActionControl")
    User = apps.get_model("auth", "User")
    for user in User.objects.all():
        ids_editions = get_ids_editions(user.id)
        for id_editions in ids_editions:
            edition = Edition.objects.get(id=id_editions)
            # import IPython; IPython.embed()
            acl_edition = acl_edition_user(apps, edition, user, Edition)
            acl = ActionControl(user=user, edition=edition, piece=edition.parent,
                                acl_view=True,
                                acl_edit="edit" in acl_edition,
                                acl_download="download" in acl_edition,
                                acl_delete="delete" in acl_edition,
                                acl_share="view" in acl_edition,
                                acl_unshare="delete" not in acl_edition
                                            and "withdraw_transfer" not in acl_edition
                                            and "withdraw_consign" not in acl_edition
                                            and "unconsign" not in acl_edition
                                            and "request_unconsign" not in acl_edition,
                                acl_transfer="transfer" in acl_edition,
                                acl_withdraw_transfer="withdraw_transfer" in acl_edition,
                                acl_consign="consign" in acl_edition,
                                acl_withdraw_consign="withdraw_consign" in acl_edition,
                                acl_unconsign="unconsign" in acl_edition,
                                acl_request_unconsign="request_unconsign" in acl_edition,
                                acl_loan="loan" in acl_edition,
                                acl_coa="coa" in acl_edition)
            acl.save()
            if len(ActionControl.objects.filter(user=user, piece=edition.parent, edition=None)) == 0:
                acl_piece = acl_piece_user(apps, edition.parent, user, Edition)
                acl = ActionControl(user=user, edition=None, piece=edition.parent,
                                    acl_view=True,
                                    acl_edit="edit" in acl_piece,
                                    acl_editions="editions" in acl_piece,
                                    acl_download="download" in acl_piece,
                                    acl_delete="delete" in acl_piece,
                                    acl_share="view" in acl_piece,
                                    acl_unshare="delete" not in acl_piece)
                acl.save()

class Migration(migrations.Migration):

    dependencies = [
        ('piece', '0014_auto_20150703_1111'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ownership', '0018_loanpiece'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionControl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('acl_view', models.BooleanField(default=False)),
                ('acl_edit', models.BooleanField(default=False)),
                ('acl_download', models.BooleanField(default=False)),
                ('acl_delete', models.BooleanField(default=False)),
                ('acl_editions', models.BooleanField(default=False)),
                ('acl_share', models.BooleanField(default=False)),
                ('acl_unshare', models.BooleanField(default=False)),
                ('acl_transfer', models.BooleanField(default=False)),
                ('acl_withdraw_transfer', models.BooleanField(default=False)),
                ('acl_consign', models.BooleanField(default=False)),
                ('acl_withdraw_consign', models.BooleanField(default=False)),
                ('acl_unconsign', models.BooleanField(default=False)),
                ('acl_request_unconsign', models.BooleanField(default=False)),
                ('acl_loan', models.BooleanField(default=False)),
                ('acl_coa', models.BooleanField(default=False)),
                ('edition', models.ForeignKey(related_name='acl_at_edition', blank=True, to='piece.Edition', null=True)),
                ('piece', models.ForeignKey(related_name='acl_at_piece', blank=True, to='piece.Piece', null=True)),
                ('user', models.ForeignKey(related_name='acl_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(
            forwards_func,
        ),
    ]
