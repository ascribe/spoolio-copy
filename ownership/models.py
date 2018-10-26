import pytz

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.postgres.fields import HStoreField
from django.utils.datetime_safe import datetime

from spool import Spoolverb

# TODO remove unused BitcoinWallet
from bitcoin.models import BitcoinTransaction, BitcoinWallet
from blobs.models import OtherData
# TODO remove unsused UserResetPasswordRole
from users.models import UserResetPasswordRole
from util import util
# TODO use explicit imports
from ownership.models_managers import *
from ownership.signals import safe_delete
from util.util import reverse_url
from webhooks.models import WebhookModel


class Ownership(WebhookModel):
    piece = models.ForeignKey('piece.Piece', related_name="ownership_at_piece")
    edition = models.ForeignKey('piece.Edition', related_name="ownership_at_edition", blank=True, null=True)
    prev_owner = models.ForeignKey(User, blank=True, null=True, related_name='ownership_from')
    new_owner = models.ForeignKey(User, blank=True, null=True, related_name='ownership_to')

    datetime = models.DateTimeField(auto_now_add=True)
    datetime_response = models.DateTimeField(blank=True, null=True)
    datetime_deleted = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    datetime_from = models.DateTimeField(blank=True, null=True)
    datetime_to = models.DateTimeField(blank=True, null=True)

    btc_tx = models.ForeignKey(BitcoinTransaction, blank=True, null=True, related_name='ownership')

    prev_btc_address = models.CharField(max_length=100, blank=True, null=True)
    new_btc_address = models.CharField(max_length=100, blank=True, null=True)

    type = models.CharField(max_length=30, blank=True, null=True)

    ciphertext_wif = models.CharField(max_length=100, blank=True, null=True)

    contract_agreement = models.ForeignKey('ContractAgreement', blank=True, null=True,
                                           related_name='ownership_at_contractagreement')

    extra_data = HStoreField(null=True)

    spool_version = 0
    verb = ''
    verb_replenish = ['ASCRIBESPOOLREPLENISH', 'RP']

    @staticmethod
    def create(cls,
               edition,
               new_owner,
               prev_owner=None,
               prev_btc_address=None,
               new_btc_address=None,
               btc_tx=None,
               ciphertext_wif=None):
        ownership = cls(
            edition=edition,
            new_owner=new_owner,
            prev_owner=prev_owner,
            prev_btc_address=prev_btc_address,
            new_btc_address=new_btc_address,
            btc_tx=btc_tx,
            ciphertext_wif=ciphertext_wif,
        )

        if prev_owner is None:
            ownership.prev_owner = edition.owner

        ownership.piece_id = edition.parent_id
        ownership.type = cls.__name__
        return ownership

    def save(self, *args, **kwargs):
        on_create = self.id is None

        super(Ownership, self).save(*args, **kwargs)

        # trigger webhook to new_owner (if any) on creation of ownership action
        if on_create and self.webhook_event:
            self.send_webhook(self.new_owner)

    @property
    def gettype(self):
        return self.__class__.__name__

    def setStatus(self, value):
        self.status = value
        self.datetime_response = timezone.now()

    @property
    def spoolverb(self):
        loan_start = self.datetime_from.strftime('%y%m%d') if self.datetime_from else ''
        loan_end = self.datetime_to.strftime('%y%m%d') if self.datetime_to else ''
        # If it is a piece it has no editions
        num_editions = self.piece.num_editions if self.piece else None
        edition_num = self.edition.edition_number if self.edition else ''
        return Spoolverb(num_editions=num_editions, edition_num=edition_num,
                         loan_start=loan_start, loan_end=loan_end)

    @property
    def from_piece_address_noPrefix(self):
        return util.remove_btc_prefix(self.prev_btc_address)

    @property
    def to_piece_address_noPrefix(self):
        return util.remove_btc_prefix(self.new_btc_address)

    def spoolify(self, verb):
        verb_version = verb[self.spool_version]
        if self.spool_version == 0:
            return verb_version
        elif self.spool_version == 1:
            return 'AS{0}{1}{2}'.format(self.spool_version, verb_version, self.piece.hashAsAddress())[:40]

    def delete_safe(self):
        self.datetime_deleted = timezone.now()
        self.save()
        safe_delete.send(sender=self.__class__, instance=self)

    def __unicode__(self):
        s = []
        if self.edition:
            s += ['bitcoin_path=%s' % self.edition.bitcoin_path]
        s += ['prev_owner=%s' % self.prev_owner]
        s += ['new_owner=%s' % self.new_owner]
        s += ['prev_btc_address=%s' % self.prev_btc_address]
        s += ['new_btc_address=%s' % self.new_btc_address]
        return unicode('; '.join(s))


class OwnershipRegistration(Ownership):
    objects = OwnershipRegistrationManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, new_owner, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = Ownership.create(cls, edition, new_owner, prev_owner, prev_btc_address, new_btc_address,
                                     btc_tx, ciphertext_wif)
        return ownership


class OwnershipEditions(Ownership):
    objects = OwnershipEditionsManager()

    class Meta:
        proxy = True

    # This is a bit different. There is no edition, only a piece
    @classmethod
    def create(cls, edition, new_owner, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = cls(piece=edition, new_owner=new_owner)
        if prev_owner is None:
            ownership.prev_owner = edition.user_registered

        ownership.type = cls.__name__
        # ACL is set in PieceFactory
        return ownership

    def __unicode__(self):
        s = []
        s += ['bitcoin_path=%s' % self.piece.bitcoin_path]
        s += ['prev_owner=%s' % self.prev_owner]
        s += ['new_owner=%s' % self.new_owner]
        s += ['prev_btc_address=%s' % self.prev_btc_address]
        s += ['new_btc_address=%s' % self.new_btc_address]
        return unicode('; '.join(s))


class OwnershipPiece(Ownership):
    objects = OwnershipPieceManager()

    class Meta:
        proxy = True

    # This is a bit different. There is no edition, only a piece
    @classmethod
    def create(cls, edition, new_owner, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = cls(piece=edition, new_owner=new_owner)
        if prev_owner is None:
            ownership.prev_owner = edition.user_registered

        ownership.type = cls.__name__
        return ownership

    def __unicode__(self):
        s = []
        s += ['bitcoin_path=%s' % self.piece.bitcoin_path]
        s += ['prev_owner=%s' % self.prev_owner]
        s += ['new_owner=%s' % self.new_owner]
        s += ['prev_btc_address=%s' % self.prev_btc_address]
        s += ['new_btc_address=%s' % self.new_btc_address]
        return unicode('; '.join(s))


class ConsignedRegistration(OwnershipPiece):
    objects = ConsignedRegistrationManager()

    class Meta:
        proxy = True


class OwnershipMigration(Ownership):
    objects = OwnershipMigrationManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, new_owner, piece=None, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):

        if edition:
            ownership = cls(edition=edition, piece=edition.parent, new_owner=new_owner)
        else:
            ownership = cls(edition=None, piece=piece, new_owner=new_owner)

        if prev_owner is None:
            if edition:
                ownership.prev_owner = edition.user_registered
            else:
                ownership.prev_owner = piece.user_registered

        ownership.type = cls.__name__
        return ownership


class OwnershipTransfer(Ownership):
    objects = OwnershipTransferManager()
    webhook_event = 'transfer.webhook'

    class Meta:
        proxy = True

    @classmethod
    def create(cls,
               edition,
               transferee,
               prev_owner=None,
               prev_btc_address=None,
               new_btc_address=None,
               btc_tx=None,
               ciphertext_wif=None):
        ownership = Ownership.create(
            cls,
            edition,
            transferee,
            prev_owner,
            prev_btc_address,
            new_btc_address,
            btc_tx,
            ciphertext_wif,
        )
        return ownership

    @property
    def webhook_data(self):
        return {
            'edition': reverse_url('api:edition-detail', args=[self.edition.bitcoin_id]),
            'transfer': reverse_url('api:ownership:ownershiptransfer-detail', args=[self.id]),
            'edition_id': self.edition.bitcoin_id,
            'previous_owner': self.prev_owner.email,
            'new_owner': self.new_owner.email
        }


# TODO: Change the name to OwnershipConsign
class Consignment(Ownership):
    objects = ConsignmentManager()
    webhook_event = 'consign.webhook'

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, consignee, owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = Ownership.create(cls, edition, consignee, owner, prev_btc_address, new_btc_address,
                                     btc_tx, ciphertext_wif)
        return ownership

    @property
    def consignee(self):
        return self.new_owner

    @property
    def webhook_data(self):
        return {
            'edition': reverse_url('api:edition-detail', args=[self.edition.bitcoin_id]),
            'consignment': reverse_url('api:ownership:consignment-detail', args=[self.id]),
            'edition_id': self.edition.bitcoin_id,
            'owner': self.prev_owner.email,
            'consignee': self.new_owner.email,
            'confirm': reverse_url('api:ownership:consignment-confirm'),
            'deny': reverse_url('api:ownership:consignment-deny')
        }


# TODO: Change name to Ownership unconsign
class UnConsignment(Ownership):
    objects = UnConsignmentManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, consignee, owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = Ownership.create(cls, edition, owner, consignee, prev_btc_address, new_btc_address,
                                     btc_tx, ciphertext_wif)

        ownership.new_btc_address = edition._most_recent_consignment.prev_btc_address
        ownership.prev_btc_address = edition._most_recent_consignment.new_btc_address
        return ownership

    @property
    def consignee(self):
        return self.new_owner


# TODO: change name to OwnershipLoan
class Loan(Ownership):
    objects = LoanManager()

    webhook_event = 'loan.webhook'

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, loanee, owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        loan = Ownership.create(cls, edition, loanee, owner, prev_btc_address, new_btc_address,
                                btc_tx, ciphertext_wif)
        return loan

    @property
    def details(self):
        return LoanDetail.objects.get(loan=self)

    @property
    def loanee(self):
        return self.new_owner

    @property
    def gallery(self):
        return self.details.gallery

    @property
    def contract(self):
        return self.details.contract

    @property
    def webhook_data(self):
        return {
            'edition': reverse_url('api:edition-detail', args=[self.edition.bitcoin_id]),
            'loan': reverse_url('api:ownership:loan-detail', args=[self.id]),
            'edition_id': self.edition.bitcoin_id,
            'owner': self.prev_owner.email,
            'loanee': self.new_owner.email,
            'confirm': reverse_url('api:ownership:loan-confirm'),
            'deny': reverse_url('api:ownership:loan-deny')
        }


class LoanPiece(Loan):
    objects = LoanPieceManager()

    @classmethod
    def create(cls, piece, loanee, owner=None, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = cls(piece=piece, new_owner=loanee)
        ownership.type = cls.__name__

        ownership.prev_owner = piece.user_registered
        ownership.prev_btc_address = piece.bitcoin_path
        return ownership

    @property
    def webhook_data(self):
        return {
            'piece': reverse_url('api:piece-detail', args=[self.piece.bitcoin_id]),
            'loan': reverse_url('api:ownership:loanpiece-detail', args=[self.id]),
            'piece_id': self.piece.bitcoin_id,
            'owner': self.prev_owner.email,
            'loanee': self.new_owner.email,
            'confirm': reverse_url('api:ownership:loanpiece-confirm'),
            'deny': reverse_url('api:ownership:loanpiece-deny')
        }


class LoanDetail(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    loan = models.ForeignKey(Loan, related_name="detail_at_loan", blank=True, null=True)
    gallery = models.TextField(blank=True, null=True)
    contract_model = models.ForeignKey('Contract', blank=True, null=True)


class Share(Ownership):
    objects = ShareManager()
    webhook_event = 'share.webhook'

    class Meta:
        proxy = True

    @classmethod
    def create(cls, edition, sharee, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = Ownership.create(cls, edition, sharee, prev_owner, prev_btc_address, new_btc_address,
                                     btc_tx, ciphertext_wif)
        return ownership

    def delete_safe(self):
        super(Share, self).delete_safe()

    @property
    def shared_user(self):
        return self.new_owner

    @shared_user.setter
    def shared_user(self, value):
        self.new_owner = value

    @property
    def webhook_data(self):
        return {
            'edition': reverse_url('api:edition-detail', args=[self.edition.bitcoin_id]),
            'share': reverse_url('api:ownership:share-detail', args=[self.id]),
            'edition_id': self.edition.bitcoin_id,
            'sharer': self.prev_owner.email,
            'sharee': self.new_owner.email
        }


class SharePiece(Share):
    objects = SharePieceManager()

    @classmethod
    def create(cls, piece, sharee, prev_owner=None,
               prev_btc_address=None, new_btc_address=None, btc_tx=None, ciphertext_wif=None):
        ownership = cls(piece=piece, new_owner=sharee)
        ownership.type = cls.__name__

        if prev_owner is None:
            ownership.prev_owner = piece.user_registered
        return ownership

    def delete_safe(self):
        super(SharePiece, self).delete_safe()

    @property
    def webhook_data(self):
        return {
            'piece': reverse_url('api:piece-detail', args=[self.piece.bitcoin_id]),
            'share': reverse_url('api:ownership:sharepiece-detail', args=[self.id]),
            'piece_id': self.piece.bitcoin_id,
            'sharer': self.prev_owner.email,
            'sharee': self.new_owner.email
        }


class License(models.Model):
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    url = models.URLField()


class ContractQuerySet(models.query.QuerySet):
    def deactivate(self, new_active_contract=None, *args, **kwargs):
        # TODO Review. It is highly likely that the code could be optimized. Mo
        # effort has been spent doing so; purpusefully, as the business logic
        # needs some clarification, after which the code will be adapted
        # accordingly, and optimizing it then, will make more sense.
        for contract in self.all():
            qs = contract.contractagreement_set.filter(datetime_deleted=None,
                                                       datetime_rejected=None)
            if new_active_contract:
                for contract_agreement in qs.filter(contract__is_public=False):
                    ContractAgreement.objects.create(
                        signee=contract_agreement.signee,
                        contract=new_active_contract,
                        appendix=contract_agreement.appendix
                    )
            qs.update(
                datetime_deleted=datetime.utcnow().replace(tzinfo=pytz.UTC)
            )
        super(ContractQuerySet, self).update(is_active=False, *args, **kwargs)


class Contract(models.Model):
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_deleted = models.DateTimeField(blank=True, null=True, default=None)
    issuer = models.ForeignKey(User)
    blob = models.ForeignKey(OtherData)
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=260, blank=False)
    is_active = models.BooleanField(default=True)

    objects = ContractQuerySet.as_manager()

    # TODO review, and perhaps return more useful information
    def __unicode__(self):
        return unicode(self.pk)

    def save(self, *args, **kwargs):
        super(Contract, self).save(*args, **kwargs)
        if self.is_public:
            # privatize" all other public contracts
            Contract.objects.filter(
                issuer=self.issuer,
                is_public=True
            ).exclude(pk=self.pk).update(is_public=False)
        if self.is_active:
            # deactivate all other active contracts
            Contract.objects.filter(
                issuer=self.issuer,
                name=self.name,
                is_active=True
            ).exclude(pk=self.pk).deactivate(new_active_contract=self)


class ContractAgreementQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(
            datetime_accepted=None,
            datetime_rejected=None,
            datetime_deleted=None)

    def accepted(self):
        return self.filter(
            datetime_accepted__isnull=False,
            datetime_rejected=None,
            datetime_deleted=None)


class ContractAgreement(models.Model):
    signee = models.ForeignKey(User)
    contract = models.ForeignKey(Contract)
    appendix = HStoreField(null=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_deleted = models.DateTimeField(blank=True, null=True, default=None)
    datetime_accepted = models.DateTimeField(blank=True, null=True, default=None)
    datetime_rejected = models.DateTimeField(blank=True, null=True, default=None)

    objects = ContractAgreementQuerySet.as_manager()

    def save(self, *args, **kwargs):
        # TODO once soft delete is integrated, verify whether datetime_deleted
        # should also be checked
        try:
            cur_obj = ContractAgreement.objects.get(pk=self.pk)
        except ContractAgreement.DoesNotExist:
            if self.datetime_accepted and self.datetime_rejected:
                raise ValidationError(
                    'Cannot both reject and accept a contract agreement!')
        else:
            if cur_obj.datetime_accepted and self.datetime_rejected:
                raise ValidationError(
                    'Cannot reject an accepted contract agreement!')
            elif cur_obj.datetime_rejected and self.datetime_accepted:
                raise ValidationError(
                    'Cannot accept a rejected contract agreement!')
        if self.signee == self.contract.issuer:
            raise ValidationError('Cannot be both signee and issuer!')
        super(ContractAgreement, self).save(*args, **kwargs)

        # set previous pending and accepted contractagreements for this signee and user to deleted
        ContractAgreement.objects.all() \
            .filter(datetime_rejected=None,
                    datetime_deleted=None,
                    contract__issuer=self.contract.issuer,
                    signee=self.signee) \
            .exclude(id=self.id) \
            .update(datetime_deleted=datetime.utcnow().replace(tzinfo=pytz.UTC))

    # TODO review, and perhaps return more useful information
    def __unicode__(self):
        return unicode(self.pk)
