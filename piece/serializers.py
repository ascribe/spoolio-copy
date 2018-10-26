import logging
import operator

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.datetime_safe import datetime

from rest_framework import serializers

from blobs.serializers import DigitalWorkSerializer, FileSerializer, ThumbnailSerializer
from blobs.models import Thumbnail
from notifications.models import EditionNotification, PieceNotification
from ownership.license_serializer import LicenseSerializer
from ownership.models import License
from piece.models import Piece, Edition
from users.serializers import UsernameSerializer

logger = logging.getLogger(__name__)


class PieceForm(serializers.ModelSerializer):
    digital_work_key = serializers.CharField(max_length=280)
    num_editions = serializers.IntegerField(required=False, default=None, allow_null=True)
    date_created = serializers.IntegerField(required=False, default=datetime.today().date().year)
    consign = serializers.BooleanField(required=False, default=False)
    license = serializers.CharField(max_length=40, required=False, default="default")
    thumbnail_file = serializers.CharField(max_length=700, required=False, allow_blank=True, allow_null=True)

    def validate_date_created(self, value):
        if value < 1:
            raise serializers.ValidationError('Please enter a valid year')
        if value > timezone.now().year:
            raise serializers.ValidationError('Creation date cannot be in the future.')
        return datetime.date(datetime(year=value, month=1, day=1))

    def validate_num_editions(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError('# editions must be a value like 1, 2, 3, ..., 10, ...')
        elif value > settings.MAX_NUM_EDITIONS:
            raise serializers.ValidationError('Maximum number of editions is %d' % settings.MAX_NUM_EDITIONS)
        return value

    def validate_license(self, value):
        if value == "":
            return None
        try:
            value = License.objects.get(code=value)
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError('License not recognized')
        return value

    def validate_thumbnail_file(self, value):
        try:
            return Thumbnail.objects.get(thumbnail_file=value, user=self.context['request'].user)
        except (Thumbnail.DoesNotExist, Exception) as e:
            logger.info(e.message)
            return None

    class Meta:
        model = Piece
        fields = ('title', 'artist_name', 'num_editions', 'date_created',
                  'digital_work_key', 'consign', 'license', 'thumbnail_file')



class PieceDeleteForm(serializers.Serializer):
    id = serializers.CharField(max_length=60)

    def validate_id(self, value):
        piece = get_piece_or_raise_error(value)
        if not piece.acl(self.context["request"].user).acl_delete:
            raise serializers.ValidationError("You don't have the appropriate rights to delete this piece")
        return piece


class MinimalPieceSerializer(serializers.ModelSerializer):
    bitcoin_id = serializers.SerializerMethodField()
    thumbnail = ThumbnailSerializer()

    def get_bitcoin_id(self, obj):
        if not obj.bitcoin_path:
            from bitcoin.models import BitcoinWallet

            new_address = BitcoinWallet.walletForUser(obj.user_registered).create_new_address()
            BitcoinWallet.import_address(new_address, obj.user_registered).delay()
            obj.bitcoin_path = new_address
            obj.save()
        return obj.bitcoin_id

    class Meta:
        model = Piece
        fields = ('id', 'title', 'artist_name', 'thumbnail', 'bitcoin_id')


class BasicPieceSerializer(MinimalPieceSerializer):
    user_registered = serializers.CharField()
    license_type = LicenseSerializer()

    acl = serializers.SerializerMethodField()

    def get_acl(self, obj):
        try:
            from acl.serializers import ActionControlSerializer

            request = self.context.get('request', None)
            return ActionControlSerializer(obj.acl(request.user)).data
        except Exception as e:
            return {'acl_view_editions': True}

    class Meta(MinimalPieceSerializer.Meta):
        fields = MinimalPieceSerializer.Meta.fields + \
                 ('num_editions', 'user_registered', 'datetime_registered', 'date_created',
                  'license_type', 'acl')


class BasicPieceSerializerWithFirstEdition(BasicPieceSerializer):
    first_edition = serializers.SerializerMethodField()

    def get_first_edition(self, obj):
        # filter for queryParams that contain 'acl_' in their key
        acl_query_params = {key: value for (key, value)
                            in self.context["request"].query_params.iteritems()
                            if 'acl_' in key}
        try:
            return obj.first_edition(self.context["request"].user, acl_query_params)
        except TypeError as e:
            return None

    class Meta(BasicPieceSerializer.Meta):
        fields = BasicPieceSerializer.Meta.fields + \
                 ('first_edition',)


class PieceSerializer(BasicPieceSerializer):
    digital_work = DigitalWorkSerializer()
    other_data = FileSerializer(many=True)

    private_note = serializers.SerializerMethodField()

    notifications = serializers.SerializerMethodField()

    def get_notifications(self, obj):
        try:
            return PieceNotification.get_notifications(obj, self.context["request"].user)
        except TypeError:
            return None

    def get_private_note(self, obj):
        request = self.context.get('request', None)
        return obj.private_note(request.user)

    class Meta(BasicPieceSerializer.Meta):
        fields = BasicPieceSerializer.Meta.fields + \
                 ('extra_data', 'digital_work', 'other_data', 'loan_history',
                  'private_note', 'public_note', 'notifications')


class PieceExtraDataForm(serializers.Serializer):
    piece_id = serializers.IntegerField()
    extradata = serializers.DictField()

    def validate(self, data):
        piece = get_piece_or_raise_error(data['piece_id'])
        self._validate_acl(piece)
        data['piece_id'] = piece
        return data

    def _validate_acl(self, piece):
        if not piece.acl(self.context["request"].user).acl_edit:
            raise serializers.ValidationError("You don't have the appropriate rights to edit this field")


class MinimalEditionSerializer(MinimalPieceSerializer):
    class Meta(MinimalPieceSerializer.Meta):
        model = Edition
        fields = MinimalPieceSerializer.Meta.fields + \
                 ('edition_number', 'bitcoin_id', 'parent')


class BasicEditionSerializer(BasicPieceSerializer):
    notifications = serializers.SerializerMethodField()

    def get_notifications(self, obj):
        return EditionNotification.get_notifications(obj, self.context["request"].user)

    class Meta:
        model = Edition
        fields = BasicPieceSerializer.Meta.fields + \
                 ('edition_number', 'bitcoin_id', 'parent', 'notifications')


class DetailedEditionSerializer(BasicEditionSerializer, PieceSerializer):
    owner = serializers.CharField()
    consignee = UsernameSerializer()

    class Meta(BasicEditionSerializer.Meta):
        fields = BasicEditionSerializer.Meta.fields + \
                 PieceSerializer.Meta.fields + \
                 ('hash_as_address', 'owner', 'btc_owner_address_noprefix',
                  'ownership_history', 'consign_history', 'coa',
                  'status', 'pending_new_owner', 'consignee')


class EditionDeleteForm(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def _validate_acl(self, edition):
        if not edition.acl(self.context["request"].user).acl_delete:
            raise serializers.ValidationError("You don't have the appropriate rights to delete this piece")

    def validate(self, data):
        editions = get_editions_or_raise_errors(data['bitcoin_id'])
        for edition in editions:
            self._validate_acl(edition)
        data['bitcoin_id'] = editions
        return data


class EditionRegister(serializers.Serializer):
    piece_id = serializers.IntegerField()
    num_editions = serializers.IntegerField()

    def validate_piece_id(self, value):
        piece = get_piece_or_raise_error(value)

        if piece.num_editions > 0:
            raise serializers.ValidationError("Piece with ID {} already has {} editions registered".format(value,
                                                                                                           piece.num_editions))
        if not piece.acl(self.context["request"].user).acl_create_editions:
            raise serializers.ValidationError("You don't have the rights to create editions")
        return piece

    def validate_num_editions(self, value):
        if value <= 0:
            raise serializers.ValidationError('# editions must be a value like 1, 2, 3, ..., 10, ...')
        elif value > settings.MAX_NUM_EDITIONS:
            raise serializers.ValidationError('Maximum number of editions is %d' % settings.MAX_NUM_EDITIONS)
        return value


def get_edition_or_raise_error(bitcoin_id):
    try:
        return Edition.objects.get(bitcoin_path__contains=bitcoin_id, datetime_deleted=None)
    except Edition.DoesNotExist:
        raise serializers.ValidationError('Edition with ID {} not found'.format(bitcoin_id))


def get_editions_or_raise_errors(bitcoin_ids):
    """
    Takes a comma separated list of bitcoin ids
    and returns their respective editions from the database.
    """
    bitcoin_ids = bitcoin_ids.split(',')

    # Source: http://stackoverflow.com/a/4824810/1263876
    editions_query = reduce(operator.or_, (Q(bitcoin_path__contains=bitcoin_id) & Q(datetime_deleted=None)
                                           for bitcoin_id in bitcoin_ids))
    editions = Edition.objects.filter(editions_query)

    editions_missing = set(bitcoin_ids) - set(edition.bitcoin_id for edition in editions)
    try:
        missing_edition = editions_missing.pop()
        raise serializers.ValidationError('Edition with ID {} not found'.format(missing_edition.bitcoin_id))
    except KeyError:
        pass
    return editions


def get_piece_or_raise_error(piece_id):
    try:
        return Piece.objects.get(id=piece_id, datetime_deleted=None)
    except Piece.DoesNotExist:
        raise serializer.ValidationError('Piece with ID {} not found'.format(piece_id))


def get_pieces_or_raise_errors(piece_ids):
    """
    Takes a comma separated list of piece ids
    and returns their respective pieces from the database.
    """
    piece_ids = map(int, piece_ids.split(','))

    # Source: http://stackoverflow.com/a/4824810/1263876
    pieces_query = reduce(operator.or_, (Q(id=piece_id) & Q(datetime_deleted=None)
                                           for piece_id in piece_ids))
    pieces = Piece.objects.filter(pieces_query)

    pieces_missing = set(piece_ids) - set(piece.id for piece in pieces)
    try:
        missing_piece = pieces_missing.pop()
        raise serializer.ValidationError('Piece with ID {} not found'.format(missing_piece.id))
    except KeyError:
        pass
    return pieces
