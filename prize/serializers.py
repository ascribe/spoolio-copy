import json
import re
from datetime import datetime

import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from acl.util import merge_acl_dict_with_object
from note.models import PrivateNote
from piece.serializers import get_edition_or_raise_error, PieceForm, BasicPieceSerializer, PieceSerializer, get_piece_or_raise_error
from prize.models import Prize, PrizeUser, PrizePiece, Rating
from users.models import UserProfile
from users.serializers import WebUserSerializer, BaseUserSerializer, UserProfileSerializer
from util.util import hash_string
from whitelabel.models import WhitelabelSettings


class PrizeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    subdomain = serializers.SerializerMethodField(read_only=True)

    def validate_num_submissions(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('The number of submissions per user must be greater than zero')
        return value

    def validate_rounds(self, value):
        if value <= 0:
            raise serializers.ValidationError('The number of rounds must be greater than zero')
        return value

    def get_name(self, obj):
        return obj.name

    def get_subdomain(self, obj):
        return obj.subdomain

    class Meta:
        model = Prize
        fields = ('whitelabel_settings', 'active', 'num_submissions', 'rounds', 'active_round', 'name', 'subdomain')


class SelectedSerializer(serializers.Serializer):
    selected = serializers.SerializerMethodField()

    def get_selected(self, obj):
        domain = self.context['request'].parser_context['kwargs']['domain_pk']
        try:
            piece_id = self.context['request'].parser_context['kwargs']['pk']
        except KeyError:
            piece_id = obj.id

        try:
            prize_piece = PrizePiece.objects.get(piece_id=piece_id, prize__whitelabel_settings__subdomain=domain)
        except ObjectDoesNotExist:
            return None

        return prize_piece.is_selected


class WebPrizeUserForm(WebUserSerializer):
    prize_name = serializers.CharField(max_length=100, required=True)

    def validate(self, data):
        # check if the prize exists
        try:
            prize = Prize.objects.get(whitelabel_settings__subdomain=data['prize_name'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError("The prize {} does not exist".format(data['prize_name']))

        # check if prize is active
        if not prize.active:
            raise serializers.ValidationError("The prize {} is not active".format(data['prize_name']))

        return data


class WebPrizeUserSerializer(serializers.ModelSerializer):
    prize = serializers.CharField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)
    email = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField(read_only=True)

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_profile(self, obj):
        try:
            user_profile = UserProfile.objects.get(user=obj.user)
        except ObjectDoesNotExist:
            user_profile = UserProfile.objects.create(user=obj.user)
            user_profile.save()
        return UserProfileSerializer(user_profile).data

    class Meta:
        model = PrizeUser
        fields = ('prize', 'username', 'email', 'is_admin', 'is_jury', 'is_judge', 'profile')


class PrizeJuryForm(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = PrizeUser
        fields = ('email',)


class WebPrizeJurySerializer(WebPrizeUserSerializer):
    status = serializers.SerializerMethodField(read_only=True)

    def get_status(self, obj):
        if obj.datetime_deleted:
            return 'Deactivated'
        if obj.user.last_login is None:
            return 'Invitation pending'
        else:
            return 'Invitation accepted'

    class Meta(WebPrizeUserSerializer.Meta):
        model = PrizeUser
        fields = WebPrizeUserSerializer.Meta.fields + ('status',)


class PrizeJuryActionForm(serializers.Serializer):
    email = serializers.EmailField()
    prize_name = serializers.CharField()

    def validate(self, data):
        user = self.context.get('request').user
        try:
            PrizeUser.objects.get(user=user,
                                  prize__whitelabel_settings__subdomain=data['prize_name'],
                                  is_admin=True,
                                  datetime_deleted=None)
        except ObjectDoesNotExist:
            raise serializers.ValidationError('You don\'t have the permissions to alter jury members')
        try:
            jury = PrizeUser.objects.get(user__email=data['email'],
                                         prize__whitelabel_settings__subdomain=data['prize_name'],
                                         is_jury=True)
        except ObjectDoesNotExist:
            raise serializers.ValidationError('User was not found in the jury list')
        data['jury'] = jury
        return data


class WebPrizePieceForm(PieceForm):
    prize_name = serializers.CharField(max_length=100, required=True)
    num_editions = serializers.IntegerField(required=False, default=None, allow_null=True, read_only=True)
    terms = serializers.NullBooleanField(write_only=True)
    extra_data = serializers.SerializerMethodField()

    def get_extra_data(self, obj):
        return _parse_extra_data(self.context.get('request', None))

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the terms of service in order to submit a piece.")
        return value

    class Meta(PieceForm.Meta):
        fields = PieceForm.Meta.fields + ('prize_name', 'extra_data', 'terms')

    def validate_prize_name(self, value):
        prize = _validate_prize(value, self.context["request"].user)
        if len(PrizePiece.objects.filter(prize=prize, user=self.context["request"].user)) >= prize.num_submissions:
            raise serializers.ValidationError(
                'You already submitted {} works to the {} prize'.format(prize.num_submissions,
                                                                        prize.name))
        return prize


class PrizePieceSubmitForm(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    prize_name = serializers.CharField(max_length=100, required=True)
    terms = serializers.NullBooleanField(write_only=True)
    extra_data = serializers.SerializerMethodField()

    def get_extra_data(self, obj):
        return _parse_extra_data(self.context.get('request', None))

    def validate_prize_name(self, value):
        return _validate_prize(value, self.context["request"].user)

    def validate_id(self, value):
        piece = get_piece_or_raise_error(value)
        user = self.context["request"].user
        if not piece.user_registered == user:
            raise serializers.ValidationError('Only the registree can submit to a prize')
        return piece

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the terms of service in order to submit a piece.")
        return value

    def validate(self, data):
        prize = data['prize_name']
        piece = data['id']
        if len(PrizePiece.objects.filter(prize=prize, piece=piece)):
            raise serializers.ValidationError('Work already submitted to the prize')
        if len(PrizePiece.objects.filter(prize=prize, user=self.context["request"].user)) >= prize.num_submissions:
            raise serializers.ValidationError(
                'You already submitted {} works to the {} prize'.format(prize.num_submissions,
                                                                        prize.name))
        return data


class WebPrizeBasicPieceSerializer(BasicPieceSerializer, SelectedSerializer):
    prize = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()

    def get_ratings(self, obj):
        try:
            request = self.context.get('request', None)
            user = request.user
            subdomain = request.parser_context['kwargs']['domain_pk']
            prize = Prize.objects.get(whitelabel_settings__subdomain=subdomain)
            prize_user = PrizeUser.objects.get(user=user, prize=prize)
            if prize_user.is_jury and not prize_user.is_judge:
                filter_kwargs = dict(piece=obj, user=user)
                if subdomain == 'portfolioreview':
                    round_two_starttime = datetime.strptime(
                        settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
                        settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
                    ).replace(tzinfo=pytz.UTC)
                    if prize.active_round == 2:
                        filter_kwargs['datetime__gte'] = round_two_starttime
                    else:
                        filter_kwargs['datetime__lt'] = round_two_starttime
                rating = Rating.objects.get(**filter_kwargs)
                return RatingSerializer(rating).data
            elif prize_user.is_judge:
                prize_piece = PrizePiece.objects.get(piece=obj, prize=prize)
                return {'average': prize_piece.average_rating, 'num_ratings': prize_piece.num_ratings}
                # request.parser_context['kwargs']['pk'] = obj.id
                # return RatingAverageSerializer(Rating.objects.filter(piece=obj), context={'request': request}).data
            return None
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None

    def get_prize(self, obj):
        try:
            return PrizeSerializer(PrizePiece.objects.get(piece=obj).prize).data
        except ObjectDoesNotExist:
            return None

    class Meta(BasicPieceSerializer.Meta):
        fields = BasicPieceSerializer.Meta.fields + ('prize', 'ratings', 'selected')


class WebPrizePieceSerializer(WebPrizeBasicPieceSerializer, PieceSerializer):
    extra_data = serializers.SerializerMethodField()
    user_registered = serializers.SerializerMethodField()
    note_from_user = serializers.SerializerMethodField()
    acl = serializers.SerializerMethodField()

    def get_extra_data(self, obj):
        try:
            prize_piece = PrizePiece.objects.get(piece=obj)
            # merging `extra_data` of Piece and PrizePiece
            extra_data = obj.extra_data.copy()
            extra_data.update(json.loads(prize_piece.extra_data))
            # also deleting `thumbnail_file` and `digital_work_key`, as we don't
            # need it
            if 'thumbnail_file' in extra_data: del extra_data['thumbnail_file']
            if 'digital_work_key' in extra_data: del extra_data['digital_work_key']
            return extra_data
        except (ObjectDoesNotExist, ValueError):
            return {}

    def get_user_registered(self, obj):
        return obj.user_registered.email

    def get_note_from_user(self, obj):
        try:
            user = self.context.get('request', None).user
            return PrizeNoteSerializer(PrivateNote.objects.get(piece=obj, user=user)).data
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None

    def get_acl(self, obj):
        try:
            from acl.serializers import ActionControlSerializer

            request = self.context.get('request', None)
            subdomain = request.parser_context['kwargs']['domain_pk']
            prize = Prize.objects.get(whitelabel_settings__subdomain=subdomain)
            settings = WhitelabelSettings.objects.get(subdomain=subdomain)
            acl = obj.acl(request.user).__dict__
            acl['acl_wallet_submit'] = (obj.user_registered == request.user and prize.active)
            # override the users acl with the whitelabel settings
            return merge_acl_dict_with_object(acl, settings)
        except Exception as e:
            if is_jury_from_request(self.context.get('request', None)):
                return {'acl_loan_request': True}
            return {}

    navigation = serializers.SerializerMethodField()

    def get_navigation(self, obj):
        request = self.context.get('request', None)
        from prize.api import PrizePieceEndpoint
        try:
            queryset = PrizePieceEndpoint.get_list_queryset(prize_name=request.parser_context['kwargs']['domain_pk'],
                                                            user=request.user).order_by('artist_name')

            index = [k for k, piece in enumerate(queryset) if piece.id == int(obj.id)]
            if not len(index):
                return None
            index = index[0]
            return {'num_items': len(queryset),
                    'prev_index': queryset[index - 1].id if index - 1 > -1 else None,
                    'next_index': queryset[index + 1].id if index + 1 < len(queryset) else None}
        except (TypeError, ValueError):
            return None

    class Meta(PieceSerializer.Meta):
        fields = PieceSerializer.Meta.fields + \
                 WebPrizeBasicPieceSerializer.Meta.fields + ('note_from_user', 'navigation')


class NoteSerializer(serializers.Serializer):
    piece_id = serializers.CharField(write_only=True, required=True)
    note = serializers.CharField(write_only=True)

    def validate_piece_id(self, value):
        return get_piece_or_raise_error(value)


class RatingSerializer(serializers.Serializer):
    rating = serializers.CharField()


class RatingAverageSerializer(SelectedSerializer):
    ratings = serializers.SerializerMethodField()
    average = serializers.SerializerMethodField()

    def get_average(self, obj):
        return Rating.average(obj)

    def get_ratings(self, obj):
        domain = self.context['request'].parser_context['kwargs']['domain_pk']
        piece_id = self.context['request'].parser_context['kwargs']['pk']

        try:
            Prize.objects.get(whitelabel_settings__subdomain=domain)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("The prize {} does not exist".format(domain))

        piece = get_piece_or_raise_error(piece_id)
        ratings = obj

        data = []
        for rating in ratings:
            try:
                note = PrivateNote.objects.get(user=rating.user, piece=piece).note
            except ObjectDoesNotExist:
                note = ''
            data.append({'user': rating.user.email, 'rating': rating.rating,
                         'note': note})

        return data


class RatingSelectSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1, required=True)
    prize_name = serializers.CharField(max_length=100, required=True)

    def validate_id(self, value):
        piece = get_piece_or_raise_error(value)
        return piece

    def validate_prize_name(self, value):
        try:
            return Prize.objects.get(whitelabel_settings__subdomain=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("The prize {} does not exist".format(value))


class PrizeNoteSerializer(serializers.Serializer):
    note = serializers.CharField()


def _parse_extra_data(request):
    exclude_fields = list(WebPrizePieceSerializer.Meta.fields) + ['terms'] + ['id']
    extra_data = {k: v for k, v in request.data.iteritems() if k not in exclude_fields}
    extra_data = json.dumps(extra_data)
    return extra_data


def _validate_prize(subdomain, user):
    # check if prize is active
    try:
        prize = Prize.objects.get(whitelabel_settings__subdomain=subdomain)
    except Prize.DoesNotExist:
        raise serializers.ValidationError("The prize {} does not exist".format(subdomain))

    # check if prize is active
    if not prize.active:
        raise serializers.ValidationError("The prize {} is not active".format(subdomain))

    # check if user is in prize
    try:
        user = PrizeUser.objects.get(user=user, prize=prize, datetime_deleted=None)
    except PrizeUser.DoesNotExist:
        PrizeUser.objects.create(prize=prize, user=user)

    return prize


def is_jury_from_request(request):
    subdomain = request.parser_context['kwargs']['domain_pk']
    try:
        PrizeUser.objects.get(user=request.user,
                              prize__whitelabel_settings__subdomain=subdomain,
                              is_jury=True,
                              datetime_deleted=None)
        return True
    except(ObjectDoesNotExist, ValueError, TypeError):
        return False
