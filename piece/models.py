from __future__ import absolute_import
from itertools import chain
from operator import attrgetter
import urllib

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import ast
import pybitcointools

from acl.models import ActionControl
from bitcoin.models import BitcoinWallet
from ownership.models import (
    OwnershipRegistration,
    Consignment,
    OwnershipTransfer,
    Share,
    Loan,
    ConsignedRegistration,
    License,
    OwnershipPiece,
    UnConsignment,
    LoanPiece,
)
from users.models import UserNeedsToRegisterRole
from util import util


class Piece(models.Model):
    title = models.CharField(max_length=180)
    artist_name = models.CharField(max_length=120)
    date_created = models.DateField()
    num_editions = models.IntegerField(default=-1)

    user_registered = models.ForeignKey(User, related_name='piece_registered')
    datetime_registered = models.DateTimeField(auto_now_add=True)

    datetime_deleted = models.DateTimeField(blank=True, null=True)
    extra_data_string = models.TextField(blank=True, default="")

    # the files themselves
    thumbnail = models.ForeignKey("blobs.Thumbnail", blank=True, null=True,
                                  related_name='thumbnail_at_piece', on_delete=models.SET_NULL)
    digital_work = models.ForeignKey("blobs.DigitalWork", related_name='digitalwork_at_piece')
    other_data = models.ManyToManyField("blobs.OtherData", blank=True,
                                        related_name='otherdata_at_piece')

    bitcoin_path = models.CharField(max_length=100, null=True, blank=True)  # genesis bitcoin address, with prefix

    license_type = models.ForeignKey(License, blank=True, null=True, related_name='license_at_piece',
                                     on_delete=models.SET_NULL)

    @property
    def extra_data(self):
        return ast.literal_eval(self.extra_data_string) if (
            self.extra_data_string and self.extra_data_string != 'None') else {}

    @extra_data.setter
    def extra_data(self, value):
        self.extra_data_string = str(value)

    @property
    def bitcoin_id(self):
        return self.bitcoin_path.split(':')[1]

    def acl(self, user):
        return ActionControl.objects.get(user=user, piece=self, edition=None)

    @property
    def editions(self):
        return Edition.objects.filter(parent_id=self.id).order_by("edition_number")

    @property
    def url(self):
        return 'pieces/' + str(self.id)

    @property
    def url_safe(self):
        return urllib.quote_plus(self.url)

    def first_edition(self, user, acl_query_params):
        queryset = ActionControl.get_items_for_user(user, acl_query_params, 'edition') \
            .filter(parent_id=self.id) \
            .order_by('edition_number')

        if not len(queryset):
            return None
        return {'bitcoin_id': queryset[0].bitcoin_id,
                'edition_number': queryset[0].edition_number,
                'num_editions_available': len(queryset)}

    def hash_as_address(self):
        data = str([
            unicode(self.title),
            unicode(self.artist_name),
            unicode(self.date_created),
            unicode(self.bitcoin_path),
            unicode(self.digital_work.hash),
        ])
        address = unicode(pybitcointools.bin_to_b58check(pybitcointools.bin_hash160(data)))
        return address

    def hash_as_address_no_metada(self):
        address = unicode(pybitcointools.bin_to_b58check(pybitcointools.bin_hash160(self.digital_work.hash)))
        return address

    def delete_safe(self):
        self.datetime_deleted = timezone.now()
        self.save()

    def loans(self, user=None, status=-1):
        # status ==-1 to skip because status None has a meaning
        if user:
            if status == -1:
                return LoanPiece.objects.filter(piece=self, new_owner=user, ciphertext_wif__isnull=False).order_by("datetime")
            else:
                return LoanPiece.objects.filter(piece=self, new_owner=user, ciphertext_wif__isnull=False, status=status).order_by("datetime")
        else:
            if status == -1:
                return LoanPiece.objects.filter(piece=self, ciphertext_wif__isnull=False).order_by("datetime")
            else:
                return LoanPiece.objects.filter(piece=self, ciphertext_wif__isnull=False, status=status).order_by("datetime")

    def loans_requests(self, user=None, status=-1):
        # status ==-1 to skip because status None has a meaning
        if user:
            if status == -1:
                return LoanPiece.objects.filter(piece=self, prev_owner=user, ciphertext_wif=None).order_by("datetime")
            else:
                return LoanPiece.objects.filter(piece=self, prev_owner=user, ciphertext_wif=None, status=status).order_by("datetime")
        else:
            if status == -1:
                return LoanPiece.objects.filter(piece=self, ciphertext_wif=None).order_by("datetime")
            else:
                return LoanPiece.objects.filter(piece=self, ciphertext_wif=None, status=status).order_by("datetime")

    @property
    def loan_history(self):
        loans = [l for l in LoanPiece.objects.filter(piece=self).order_by("datetime") if l.status != 0]
        return Piece.render_loan_history(loans)

    def private_note(self, user):
        if not user or isinstance(user, AnonymousUser):
            return None
        from note.models import PrivateNote

        try:
            note = PrivateNote.objects.get(piece=self, edition=None, user=user)
            return note.note
        except ObjectDoesNotExist as e:
            return None

    @property
    def public_note(self):
        from note.models import PublicNote

        try:
            note = PublicNote.objects.get(piece=self, edition=None)
            return note.note
        except ObjectDoesNotExist as e:
            return None

    @staticmethod
    def render_loan_history(loans):
        history_list = []
        for l in loans:
            loan_date = l.datetime.strftime('%b. %d, %Y, %X')
            loan_text = u"Loaned to {} from {} to {}{}".format(l.new_owner.username,
                                                               l.datetime_from.strftime('%b. %d, %Y'),
                                                               l.datetime_to.strftime('%b. %d, %Y'),
                                                               " (pending)" if l.status is None else "")

            # if there is a ContractAgreement linked to a loan,
            # we want to append the loan_text shown in "Loan History"
            # and provide the user with a url to that contract
            if l.contract_agreement:
                contract = l.contract_agreement.contract
                loan_text += u' under the contract "{}"'.format(contract.name)
                history_list.append((loan_date, loan_text, contract.blob.url_safe))
            else:
                history_list.append((loan_date, loan_text))
        return history_list


class Edition(models.Model):
    parent = models.ForeignKey("piece.Piece", related_name='piece_at_edition')
    edition_number = models.IntegerField()

    # bitcoin
    bitcoin_path = models.CharField(max_length=100)  # genesis bitcoin address, with prefix
    datetime_deleted = models.DateTimeField(blank=True, null=True)
    # the files themselves
    coa = models.ForeignKey("coa.CoaFile", blank=True, null=True, related_name='coafile_at_piece',
                            on_delete=models.SET_NULL)

    # the users (owner, registree, consignee) involved in this piece
    pending_new_owner = models.ForeignKey(User, blank=True, null=True, related_name='pending_piece_owned',
                                          on_delete=models.SET_NULL)
    owner = models.ForeignKey(User, blank=True, null=True, related_name='piece_owned',
                              on_delete=models.SET_NULL)
    consignee = models.ForeignKey(User, blank=True, null=True, related_name='pending_piece_consigned',
                                  on_delete=models.SET_NULL)

    consign_status = models.IntegerField(choices=settings.CONSIGN_STATUS_CHOICES, default=settings.NOT_CONSIGNED)

    @property
    def artist_name(self):
        return self.parent.artist_name

    @property
    def title(self):
        return self.parent.title

    @property
    def extra_data(self):
        return self.parent.extra_data

    @property
    def date_created(self):
        return self.parent.date_created

    @property
    def num_editions(self):
        return self.parent.num_editions

    @property
    def user_registered(self):
        return self.parent.user_registered

    @property
    def datetime_registered(self):
        return self.parent.datetime_registered

    @property
    def thumbnail(self):
        return self.parent.thumbnail

    @property
    def digital_work(self):
        return self.parent.digital_work

    @property
    def other_data(self):
        return self.parent.other_data

    @property
    def license_type(self):
        return self.parent.license_type

    @property
    def bitcoin_id(self):
        if ':' in self.bitcoin_path:
            return self.bitcoin_path.split(':')[1]
        return self.bitcoin_path

    @property
    def btc_owner_address(self):
        t = self._most_recent_transfer
        if t is not None and t.new_btc_address is not None:
            return t.new_btc_address
        else:
            return self.bitcoin_path

    @property
    def btc_owner_address_noprefix(self):
        return util.remove_btc_prefix(self.btc_owner_address)

    @property
    def ownership_history(self):
        """@return -- list of (date, action_str)"""
        history = []
        history.append((self.datetime_registered.strftime('%b. %d, %Y, %X'),
                  u"Registered by {}".format(self.user_registered)))
        transfers = OwnershipTransfer.objects.filter(edition=self, datetime_deleted=None).order_by("datetime")

        for t in transfers:
            history.append((t.datetime.strftime('%b. %d, %Y, %X'),
                      u'Transferred to {}'.format(t.new_owner.username)))

        try:
            UserNeedsToRegisterRole.objects.get(user=transfers.last().new_owner, type="UserNeedsToRegisterRole")
        except (UserNeedsToRegisterRole.DoesNotExist, AttributeError):
            # If the user is either fully registered or there are no
            # transfers for the edition yet, we just return the
            # registration action as the only element of the history
            pass
        else:
            date, action_str = history[-1]
            history[-1] = (date, ''.join([action_str, ' (pending)']))
        return history

    @property
    def consign_history(self):
        """@return -- list of (date, action_str)"""
        h = []
        consigns = Consignment.objects.filter(edition=self).exclude(status=0)
        unconsigns = UnConsignment.objects.filter(edition=self).exclude(status=0)
        result_list = sorted(
            chain(consigns, unconsigns),
            key=attrgetter('datetime'))
        for c in result_list:
            pending = "(pending)" if c.status is None else ""
            type = "Consigned" if c.type == "Consignment" else "Unconsigned"
            h.append((c.datetime.strftime('%b. %d, %Y, %X'),
                      u"{} to {} {}".format(type, c.new_owner.username, pending)))
        return h

    @property
    def loan_history(self):
        """@return -- list of (date, action_str)"""
        loans = [l for l in Loan.objects.filter(edition=self).order_by("datetime") if l.status != 0]
        return Piece.render_loan_history(loans)

    @property
    def shared_users(self):
        return [s for s in Share.objects.filter(edition=self) if not s.shared_user == self.owner]

    @property
    def siblings(self):
        """@return -- list of pieces with same root piece (i.e. all editions)"""
        return Edition.objects.filter(parent=self.parent)

    @property
    def status(self):
        status = []
        if self.pending_new_owner is not None:
            status += ["pending_transfer"]
        if self.consign_status == settings.CONSIGNED:
            status += ["consigned"]
        if self.consign_status == settings.PENDING_CONSIGN:
            status += ["pending_consign"]
        if self.consign_status == settings.PENDING_UNCONSIGN:
            status += ["pending_unconsign"]
        if self.loans(status=None):
            status += ["pending_loan"]
        return status

    @property
    def url(self):
        return 'editions/' + self.bitcoin_id

    @property
    def url_safe(self):
        return urllib.quote_plus(self.url)

    @property
    def yearAndEdition_str(self):
        return u'%s, %d/%d' % (str(self.date_created.year), self.edition_number, self.num_editions)

    @property
    def _most_recent_transfer(self):
        # could also calculate this via the chain of bitcoin addresses
        # (and that could be done independently of the DB, using the blockchain)
        # TODO: do we need the exclude? A: yes for btc_owner_address, but might miss some transfers
        transfers = OwnershipTransfer.objects.filter(edition=self).exclude(btc_tx=None).order_by("datetime")
        n_transfers = len(transfers)
        if n_transfers > 0:
            return transfers[n_transfers - 1]
        else:
            return None

    @property
    def _most_recent_consignment(self):
        # could also calculate this via the chain of bitcoin addresses
        # (and that could be done independently of the DB, using the blockchain)
        consignments = Consignment.objects.filter(edition=self).exclude(status=0).order_by("datetime")
        n_consignments = len(consignments)
        if n_consignments > 0:
            return consignments[n_consignments - 1]
        else:
            return None

    def acl(self, user):
        return ActionControl.objects.get(user=user, edition=self)

    def delete_safe(self):
        self.datetime_deleted = timezone.now()
        self.save()

    def hash_as_address(self):
        """
        @return
          btc_address -- address that has a hash of all the info about the piece.

        @notes

        Steps:
        1. Hash the data using sha256.
        2. The hash is hashed again using ripemd160*.
        3. The version byte (0x00 for main net) is added to the beginning.
        4. The checksum, which is the first 4 bytes of sha256(sha256(versioned_hash)))*,
         is added to the end.
        5. Finally, everything is converted to base58.

          * Note that when hashing is applied on hashes, the actual hash is being hashed,
            and not the hexadecimal representation of the hash.

        -The steps are from https://www.btproof.com/technical.html
        -Below, the steps are implemented with the help of pybitcointools.

        -The hash is *not* unique per edition, so that we can have a single bitcoin
         transaction to register > 1 pieces, all with the same hash.
        """
        assert 'placeholder' not in self.bitcoin_path
        data = str([
            unicode(self.title),
            unicode(self.artist_name),
            unicode(self.date_created),
            unicode(self.num_editions),
            unicode(self.bitcoin_path),
            unicode(self.digital_work.hash),
        ])
        address = unicode(pybitcointools.bin_to_b58check(pybitcointools.bin_hash160(data)))
        return address

    def hash_as_address_no_metada(self):
        address = unicode(pybitcointools.bin_to_b58check(pybitcointools.bin_hash160(self.digital_work.hash)))
        return address

    def loans(self, user=None, status=-1):
        # status ==-1 to skip because status None has a meaning
        if user:
            if status == -1:
                return Loan.objects.filter(edition=self, new_owner=user).order_by("datetime")
            else:
                return Loan.objects.filter(edition=self, new_owner=user, status=status).order_by("datetime")
        else:
            if status == -1:
                return Loan.objects.filter(edition=self).order_by("datetime")
            else:
                return Loan.objects.filter(edition=self, status=status).order_by("datetime")

    def note_from_user(self, user):
        if not user or isinstance(user, AnonymousUser):
            return None
        from note.models import PrivateNote

        try:
            note = PrivateNote.objects.get(edition=self, user=user)
            return note.note
        except ObjectDoesNotExist as e:
            return None

    def private_note(self, user):
        if not user or isinstance(user, AnonymousUser):
            return None
        from note.models import PrivateNote

        try:
            note = PrivateNote.objects.get(piece=self.parent, edition=self, user=user)
            return note.note
        except ObjectDoesNotExist as e:
            return None

    @property
    def public_note(self):
        from note.models import PublicNote

        try:
            note = PublicNote.objects.get(piece=self.parent, edition=self)
            return note.note
        except ObjectDoesNotExist as e:
            return None

    def __unicode__(self):
        return unicode(self.bitcoin_id)


class PieceFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def register(param, user):
        from encoder import zencoder_api
        from piece.tasks import register_editions

        try:
            print u"create master proof %s" % param['title']
        except:
            pass
        # TODO: Use snail-case naming of variables
        rootPiece = PieceFactory._createPieceInDB(user,
                                                  param['title'],
                                                  param['artist_name'],
                                                  param['date_created'],
                                                  param['thumbnail'],
                                                  param['digital_work'],
                                                  param['license'])

        if param['consign']:
            piece_registration = ConsignedRegistration.create(edition=rootPiece, new_owner=user)
        else:
            piece_registration = OwnershipPiece.create(edition=rootPiece, new_owner=user)
        piece_registration.save()

        # register number of editions
        if param['num_editions'] and param['num_editions'] > 0:
            register_editions(rootPiece, rootPiece.user_registered, param['num_editions']).delay()

        if rootPiece.digital_work.mime == 'video':
            zencoder_api.encode(user, rootPiece.digital_work)

        return rootPiece

    @staticmethod
    def _createPieceInDB(user,
                         title,
                         artist_name,
                         date_created,
                         thumbnail,
                         digital_work,
                         license_type,
                         extra_data={},
                         other_data=None):

        new_address = BitcoinWallet.walletForUser(user).create_new_address()
        BitcoinWallet.import_address(new_address, user).delay()

        piece = Piece(title=title,
                      artist_name=artist_name,
                      date_created=date_created,
                      extra_data=extra_data,
                      user_registered=user,
                      thumbnail=thumbnail,
                      digital_work=digital_work,
                      bitcoin_path=new_address,
                      license_type=license_type)
        if other_data:
            piece.other_data.add(other_data)
        piece.save()
        return piece

# =========================================================================================
def editableSiblingEditionsFromID(user, bitcoin_id):
    # all editions
    try:
        edition = Edition.objects.get(owner=user, bitcoin_id=bitcoin_id)
        if edition and edition.canEdit(user):
            return edition.siblings
    except ObjectDoesNotExist as e:
        pass
    return []
