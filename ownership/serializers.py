from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import serializers

from acl.models import ActionControl
from blobs.models import OtherData
from blobs.serializers import FileSerializer
from bitcoin.serializers import BitcoinTransactionSerializer
from core.fields import SlugRelatedField, CommaSeparatedEmailField
from ownership.fields import ContractRelatedField
from ownership.models import (
    Share,
    Consignment,
    OwnershipTransfer,
    SharePiece,
    Loan,
    Contract,
    ContractAgreement
)
from piece.serializers import (
    MinimalPieceSerializer,
    MinimalEditionSerializer,
    get_edition_or_raise_error,
    get_editions_or_raise_errors,
    get_piece_or_raise_error,
    get_pieces_or_raise_errors
)

from users.api import createOrGetUser
from users.serializers import verify_password, USER_PASSWORD_MAX_LENGTH


class OwnershipSerializer(serializers.Serializer):
    """Serializer for the Ownership model.

    Neither includes Piece nor Edition. Please use
    specific Ownership serializers as described in the following
    examples.

    Examples:
        Serializing an action that involves an edition:

            >>> transfer = OwnershipTransfer(edition, transferee, prev_owner)
            >>> serializer = OwnershipEditionSerializer(transfer)

        Serializing an action that involves a piece:

            >>> loan_piece = LoanPiece(piece, loanee, prev_owner)
            >>> serializer = OwnershipPieceSerializer(loan_piece)
    """
    id = serializers.IntegerField()
    type = serializers.CharField()

    datetime = serializers.DateTimeField()
    btc_tx = BitcoinTransactionSerializer()

    new_owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='email'
    )
    prev_owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='email'
    )

    new_btc_address = serializers.CharField()
    prev_btc_address = serializers.CharField()

    status = serializers.IntegerField()


class OwnershipEditionSerializer(OwnershipSerializer):
    edition = MinimalEditionSerializer()


class LoanSerializer(OwnershipEditionSerializer):
    startdate = serializers.DateTimeField(source='datetime_from', format='%Y-%m-%d', required=False)
    enddate = serializers.DateTimeField(source='datetime_to', format='%Y-%m-%d', required=False)


class OwnershipPieceSerializer(OwnershipSerializer):
    piece = MinimalPieceSerializer()


class LoanPieceSerializer(OwnershipPieceSerializer):
    startdate = serializers.DateTimeField(source='datetime_from', format='%Y-%m-%d', required=False)
    enddate = serializers.DateTimeField(source='datetime_to', format='%Y-%m-%d', required=False)


class TransferModalForm(serializers.ModelSerializer):
    transferee = serializers.EmailField(required=True)
    transfer_message = serializers.CharField(required=False, default="")
    bitcoin_id = serializers.CharField(min_length=30)
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)
    extra_data = serializers.DictField(required=False, allow_null=True)

    def validate_transferee(self, value):
        value = value.lower()
        user = self.context["request"].user
        if value == user.email:
            raise serializers.ValidationError("You can't transfer to yourself!")
        return value

    def validate_password(self, value):
        return verify_password(self.context["request"].user.username, password=value)

    def _validate_acl(self, edition, transferee):
        try:
            acl = ActionControl.objects.get(
                user=self.context['request'].user, edition=edition)
        except ActionControl.DoesNotExist:
            acl = None

        if not acl or not acl.acl_transfer:
            raise serializers.ValidationError(
                {'bitcoin_id': "You don't have the rights to transfer this edition"})

        if transferee in [edition.owner.username, edition.owner.email]:
            raise serializers.ValidationError({"bitcoin_id": "You can't transfer to the owner!"})

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])
        for edition in editions:
            self._validate_acl(edition, data['transferee'])
        data['bitcoin_id'] = editions
        return data

    class Meta:
        model = OwnershipTransfer
        fields = ('transferee', 'transfer_message', 'bitcoin_id', 'password', 'extra_data')


class TransferWithdrawForm(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate(self, data):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(data['bitcoin_id'])
        if not edition.owner == user:
            raise serializers.ValidationError("You are not allowed to withdraw the transfer")
        if edition.pending_new_owner is None:
            raise serializers.ValidationError("This transfer is not pending")
        transfers = OwnershipTransfer.objects.filter(edition=edition).order_by("datetime")
        transfer = transfers[len(transfers) - 1]
        if not transfer.new_owner == edition.pending_new_owner:
            raise serializers.ValidationError("This transfer is not pending")
        data['bitcoin_id'] = edition
        data['transfer'] = transfer
        return data


class ContractAgreementSerializerMixin(object):

    def validate_contract_agreement_id(self, value):
        if not value:
            return None
        try:
            value = ContractAgreement.objects.get(id=value)
        except ContractAgreement.DoesNotExist:
            raise serializers.ValidationError('Contract agreement with id {} not found'.format(value))
        if value.datetime_deleted or value.datetime_rejected:
            raise serializers.ValidationError("Invalid contract agreement")
        return value

    def _validate_contract_agreement(self, contract_agreement, user_email):
        if contract_agreement:
            if self.context["request"].user not in [contract_agreement.signee, contract_agreement.contract.issuer]:
                raise serializers.ValidationError("Invalid contract agreement")
            if user_email not in [contract_agreement.signee.email, contract_agreement.contract.issuer.email]:
                raise serializers.ValidationError("Invalid contract agreement")


class ConsignModalForm(serializers.ModelSerializer, ContractAgreementSerializerMixin):
    consignee = serializers.EmailField(required=True)
    consign_message = serializers.CharField(required=False, default="")
    bitcoin_id = serializers.CharField(min_length=30)
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)
    terms = serializers.NullBooleanField(write_only=True,
                                         required=False,
                                         default=True)
    contract_agreement_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError('You must accept the terms and conditions.')
        return value

    def validate_consignee(self, value):
        value = value.lower()
        user = self.context["request"].user
        if value == user.email:
            raise serializers.ValidationError("You can't consign to yourself!")
        return value

    def validate_password(self, value):
        return verify_password(self.context["request"].user.username, password=value)

    def _validate_acl(self, edition, consignee):
        if not edition.acl(self.context["request"].user).acl_consign:
            raise serializers.ValidationError(
                {"bitcoin_id": "You don't have the appropriate rights to consign this piece"})
        if consignee in [edition.owner.username, edition.owner.email]:
            raise serializers.ValidationError({"bitcoin_id": "You can't consign to the owner!"})

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])
        for edition in editions:
            self._validate_acl(edition, data['consignee'])
        data['bitcoin_id'] = editions
        if 'contract_agreement_id' in data.keys():
            self._validate_contract_agreement(data['contract_agreement_id'], data['consignee'])
        else:
            data['contract_agreement_id'] = None
        return data

    class Meta:
        model = Consignment
        fields = ('consignee', 'consign_message', 'bitcoin_id', 'password', 'contract_agreement_id', 'terms')


class ConsignConfirmSerializer(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_bitcoin_id(self, data):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(data)
        if not edition.consignee == user:
            raise serializers.ValidationError("You are not allowed to confirm this consignment")
        if edition.consign_status != settings.PENDING_CONSIGN:
            raise serializers.ValidationError("This piece is not pending for actions")
        return edition


class ConsignWithdrawForm(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate(self, data):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(data['bitcoin_id'])
        if not edition.owner == user:
            raise serializers.ValidationError("You are not allowed to withdraw the consignment")
        if not edition.consign_status == settings.PENDING_CONSIGN:
            raise serializers.ValidationError("This consignment is not pending")
        data['bitcoin_id'] = edition
        data['consigment'] = edition._most_recent_consignment
        return data


class UnConsignModalForm(serializers.Serializer):
    unconsign_message = serializers.CharField(required=False, default="")
    bitcoin_id = serializers.CharField(min_length=30)
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)

    def validate_password(self, value):
        return verify_password(self.context["request"].user.username, password=value)

    def _validate_acl(self, edition, user):
        if not edition.consignee == user:
            raise serializers.ValidationError(
                {"bitcoin_id": "You don't have the appropriate rights to unconsign this piece"})
        if not edition.consign_status in [settings.CONSIGNED, settings.PENDING_UNCONSIGN]:
            raise serializers.ValidationError({"bitcoin_id": "This piece is not consigned"})

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])
        for edition in editions:
            self._validate_acl(edition, self.context["request"].user)
        data['bitcoin_id'] = editions
        return data


class UnConsignRequestSerializer(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)
    unconsign_request_message = serializers.CharField(required=False, default="")

    def validate_bitcoin_id(self, value):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(value)
        if not edition.owner.username in [user.username, user.email]:
            raise serializers.ValidationError("You are not allowed to request unconsignment")
        if edition.consign_status == settings.PENDING_UNCONSIGN:
            raise serializers.ValidationError("Previous request still pending")
        if edition.consign_status != settings.CONSIGNED:
            raise serializers.ValidationError("This piece is not consigned")
        return edition


class UnConsignDenySerializer(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_bitcoin_id(self, value):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(value)
        if edition.consignee != user:
            raise serializers.ValidationError("You are not allowed to deny this unconsignment")
        if edition.consign_status != settings.PENDING_UNCONSIGN:
            raise serializers.ValidationError("This piece is not pending unconsignment")
        return edition


class LoanModalForm(serializers.Serializer, ContractAgreementSerializerMixin):
    loanee = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)
    bitcoin_id = serializers.CharField(min_length=30)

    gallery = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200, default="")
    loan_message = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    startdate = serializers.DateField(initial=timezone.now().date)
    enddate = serializers.DateField(initial=timezone.now().date)

    terms = serializers.NullBooleanField(write_only=True,
                                         error_messages={'required': 'You must accept the terms and conditions.'},
                                         label='Terms')
    contract_agreement_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError('You must accept the terms and conditions.')
        return value

    def validate_loanee(self, value):
        value = value.lower()
        user = self.context["request"].user
        if value == user.email:
            raise serializers.ValidationError("You can't loan to yourself!")
        return value

    def validate_password(self, value):
        return verify_password(self.context["request"].user.username, password=value)

    def _validate_acl(self, edition, loanee):
        if not edition.acl(self.context["request"].user).acl_loan:
            raise serializers.ValidationError(
                {"bitcoin_id": "You don't have the appropriate rights to loan this edition"})
        if loanee in [edition.owner.username, edition.owner.email, edition.consignee]:
            raise serializers.ValidationError({"bitcoin_id": "You can't loan to the owner or consignee!"})

        # check if the edition is already loaned to the loanee
        try:
            loanee_user = User.objects.get(email=loanee)
            loans = edition.loans()
            for loan in loans:
                if loan.loanee == loanee_user and loan.datetime_to > timezone.now():
                    raise serializers.ValidationError("edition {} already loaned to {} until {}".format(
                        edition.edition_number, loanee, loan.datetime_to.strftime("%Y-%m-%d")))
        except ObjectDoesNotExist:
            # its ok. The loanee does not exist in our db yet. the api endpoint will send him an email
            pass

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])

        for edition in editions:
            self._validate_acl(edition, data['loanee'].lower())

        if data['startdate'] >= data['enddate']:
            raise serializers.ValidationError(
                {"enddate": "The end date of the loan has to be later than the start date"})
        data['bitcoin_id'] = editions
        if 'contract_agreement_id' in data.keys():
            self._validate_contract_agreement(data['contract_agreement_id'], data['loanee'])
        else:
            data['contract_agreement_id'] = None
        return data


class LoanDenySerializer(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_bitcoin_id(self, value):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(value)
        loan = edition.loans(user=user, status=None)
        if len(loan) == 0:
            raise serializers.ValidationError("Loan not found")
        return edition


class LoanPieceModalForm(LoanModalForm):
    piece_id = serializers.CharField(required=True)
    bitcoin_id = serializers.CharField(required=False)

    def validate(self, data):
        # Only one piece at a time can be loaned.
        # Whereas multiple editions can be loaned at once
        piece = get_piece_or_raise_error(data['piece_id'])
        self._validate_acl(piece, data['loanee'].lower())
        data['piece_id'] = piece

        if data['startdate'] >= data['enddate']:
            raise serializers.ValidationError(
                {"enddate": "The end date of the loan has to be later than the start date"})
        if 'contract_agreement_id' in data.keys():
            self._validate_contract_agreement(data['contract_agreement_id'], data['loanee'])
        else:
            data['contract_agreement_id'] = None
        return data

    def _validate_acl(self, piece, loanee):
        # TODO Review. Quick fix for issue #165.
        try:
            acl = ActionControl.objects.get(
                user=self.context["request"].user, piece=piece, edition=None)
        except ActionControl.DoesNotExist:
            acl = None
        if not acl or not acl.acl_loan:
            raise serializers.ValidationError(
                {"piece_id": "You don't have the appropriate rights to loan this piece"})
        if loanee in [piece.user_registered.username, piece.user_registered.email]:
            raise serializers.ValidationError({"piece_id": "You can't loan to the owner!"})

        # check if the piece is already loaned to the loanee
        try:
            loanee_user = User.objects.get(email=loanee)
            loans = piece.loans()
            for loan in loans:
                if loan.loanee == loanee_user and loan.datetime_to > timezone.now():
                    raise serializers.ValidationError("piece {} already loaned to {} until {}".format(
                        piece.id, loanee, loan.datetime_to.strftime("%Y-%m-%d")))
        except ObjectDoesNotExist:
            # its ok. The loanee does not exist in our db yet. the api endpoint will send him an email
            pass

    class Meta:
        model = Loan
        fields = ('piece_id', 'loanee', 'password', 'gallery', 'loan_message',
                  'startdate', 'enddate', 'contract_key', 'terms', 'contract_agreement_id')


class LoanPieceDenySerializer(serializers.Serializer):
    piece_id = serializers.CharField(required=True)

    def validate_piece_id(self, value):
        user = self.context["request"].user
        piece = get_piece_or_raise_error(value)
        loan = piece.loans(user=user, status=None)
        if len(loan) == 0:
            raise serializers.ValidationError("Loan not found")
        return piece


class LoanPieceRequestSerializer(serializers.Serializer):
    piece_id = serializers.CharField(required=True)
    gallery = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200, default="")

    # write only
    loan_message = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="", write_only=True)
    startdate = serializers.DateField(initial=timezone.now().date, write_only=True)
    enddate = serializers.DateField(initial=timezone.now().date, write_only=True)
    contract_key = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=280, default="",
                                         write_only=True)
    terms = serializers.NullBooleanField(write_only=True,
                                         error_messages={'required': 'You must accept the terms and conditions.'},
                                         label='Terms')

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError('You must accept the terms and conditions.')
        return value

    def validate(self, data):
        pieces = get_pieces_or_raise_errors(data['piece_id'])

        # TODO: Add acl for loan_request
        # for piece in pieces:
        #     self._validate_acl(piece, data['loanee'].lower())
        data['piece_id'] = pieces

        if data['startdate'] >= data['enddate']:
            raise serializers.ValidationError(
                {"enddate": "The end date of the loan has to be later than the start date"})
        return data

    # read only
    datetime_from = serializers.DateTimeField(read_only=True)
    datetime_to = serializers.DateTimeField(read_only=True)
    prev_owner = serializers.SerializerMethodField(read_only=True)
    new_owner = serializers.SerializerMethodField(read_only=True)

    def get_prev_owner(self, obj):
        if obj.prev_owner:
            return obj.prev_owner.email
        return None

    def get_new_owner(self, obj):
        if obj.new_owner:
            return obj.new_owner.email
        return None


class LoanPieceRequestConfirmSerializer(serializers.Serializer):
    piece_id = serializers.CharField(required=True)
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)

    def validate_piece_id(self, value):
        user = self.context["request"].user
        piece = get_piece_or_raise_error(value)
        loan = piece.loans_requests(user=user, status=None)
        if len(loan) == 0:
            raise serializers.ValidationError("Loan not found")
        return piece

    def validate_password(self, value):
        return verify_password(self.context["request"].user.username, password=value)


class LoanPieceRequestDenySerializer(LoanPieceRequestConfirmSerializer):
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH, required=False)


class BlobRelatedField(SlugRelatedField):
    def to_representation(self, obj):
        return FileSerializer(obj).data


class ContractForm(serializers.ModelSerializer):
    issuer = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CreateOnlyDefault(serializers.CurrentUserDefault())
    )
    blob = BlobRelatedField(
        slug_field='other_data_file',
        required=False,
        queryset=OtherData.objects.all()
    )

    class Meta:
        model = Contract


class ContractSerializer(ContractForm):
    issuer = serializers.SerializerMethodField()
    blob = FileSerializer(read_only=True)

    def get_issuer(self, obj):
        return obj.issuer.email


class ContractAgreementForm(serializers.ModelSerializer):
    signee = serializers.EmailField(required=False, allow_null=True)

    contract = ContractRelatedField(
        required=True,
        queryset=Contract.objects.filter()
    )

    def validate_signee(self, value):
        if value is None:
            value = self.context['request'].user.email
        try:
            value = User.objects.get(email=value)
        except User.DoesNotExist:
            value = createOrGetUser(value)
        return value

    def validate(self, data):
        # request user triggers the create agreement
        if ('signee' in data.keys() and data['signee'] == self.context['request'].user
            and not data['contract'].is_public):
            raise serializers.ValidationError('A signee can only create agreements with public contracts')
        return data

    class Meta:
        model = ContractAgreement


class ContractAgreementSerializer(ContractAgreementForm):
    contract = ContractSerializer()


class ShareForm(serializers.ModelSerializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_bitcoin_id(self, value):
        user = self.context["request"].user
        piece = get_edition_or_raise_error(value)
        if not piece.canAddToPieces(user):
            raise serializers.ValidationError("You don't have the appropriate rights to add this artwork to your list")
        return value

    class Meta:
        model = Share
        fields = ('bitcoin_id',)


class ShareModalForm(serializers.ModelSerializer):
    share_emails = CommaSeparatedEmailField()
    share_message = serializers.CharField(required=False, default="", allow_blank=True)
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_share_emails(self, value):
        user = self.context['request'].user
        if user.email in value:
            raise serializers.ValidationError("You can't share with yourself!")
        users = []
        for email in value:
            users.append(createOrGetUser(email))
        return users

    def validate(self, data):
        data['bitcoin_id'] = get_editions_or_raise_errors(data['bitcoin_id'])
        return data

    class Meta:
        model = Share
        fields = ('share_emails', 'share_message', 'bitcoin_id')


class ShareDeleteForm(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def _validate_acl(self, edition, user):
        share = Share.objects.filter(new_owner=user, edition=edition, datetime_deleted=None)
        if len(share) == 0:
            pass
            # raise serializers.ValidationError("This piece is not shared with you.")

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])
        user = self.context['request'].user
        for edition in editions:
            self._validate_acl(edition, user)
        data['bitcoin_id'] = editions
        return data


class SharePieceModalForm(ShareModalForm):
    piece_id = serializers.IntegerField(min_value=1)

    def validate(self, data):
        data['piece_id'] = get_piece_or_raise_error(data['piece_id'])
        return data

    class Meta:
        model = SharePiece
        fields = ('share_emails', 'share_message', 'piece_id')


class SharePieceDeleteForm(serializers.Serializer):
    piece_id = serializers.IntegerField(min_value=1)

    def validate(self, data):
        data['piece_id'] = get_piece_or_raise_error(data['piece_id'])
        return data
