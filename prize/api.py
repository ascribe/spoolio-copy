from datetime import datetime

import pytz

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError
from django.db.models import Q

from rest_framework.decorators import detail_route, list_route
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from .models import Rating
from core.api import AscribeModelViewSet
from note.api import NoteEndpoint
from acl.models import ActionControl
from piece.models import Piece
from piece.api import PieceEndpoint
from prize.permissions import IsAuthenticatedAndAdmin, IsAuthenticatedAndJury
from piece.serializers import PieceForm
# TODO >>> import this
#      ...
#      Explicit is better than implicit.
from prize.serializers import *
from prize.serializers import WebPrizePieceForm

from users.api import UserEndpoint, createOrGetUser
from users.models import UserValidateEmailRole, UserNeedsToRegisterRole
from users.permissions import IsAuthenticatedOrSignUpOnly
from users.serializers import WebUserSerializer
from util.util import extract_subdomain
from web.api_util import PaginatedGenericViewSetKpi     # TODO remove - unused

# TODO: Refactor all email endpoints for sluice to generic endpoints for prizes in general
from emails.tasks import (
    email_submit_prize,
    email_signup_judge,
    email_invite_judge,
)


class RatingOrdeningFilter(filters.OrderingFilter):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            if 'note_at_piece' in ordering or 'selected' in ordering:
                prize = Prize.objects.get(whitelabel_settings__subdomain=request.parser_context['kwargs']['domain_pk'])
                prize_user = PrizeUser.objects.get(user=request.user, prize=prize)
                # order by personal rating
                if prize_user.is_jury and not prize_user.is_judge and 'note_at_piece' in ordering:
                    user_ratings = Rating.objects.filter(user=request.user).order_by('-note')
                    pk_list = [r.piece.id for r in user_ratings]
                # order by average rating
                elif prize_user.is_jury and prize_user.is_judge and 'note_at_piece' in ordering:
                    average_ratings = PrizePiece.objects.filter(prize=prize).order_by('-average_rating')
                    pk_list = [r.piece.id for r in average_ratings if r.average_rating is not None]
                # order by selected
                elif (prize_user.is_jury or prize_user.is_judge or prize_user.is_admin) and 'selected' in ordering:
                    selected = PrizePiece.objects.filter(prize=prize).order_by('is_selected')
                    pk_list = [r.piece.id for r in selected if r.is_selected is True]
                else:
                    return queryset.order_by(*ordering)
                if pk_list:
                    clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(pk_list)])
                    ordering = 'CASE %s END' % clauses
                    queryset_rated = queryset.filter(pk__in=pk_list) \
                        .extra(select={'ordering': ordering}, order_by=('ordering', 'title'))
                    return queryset_rated | queryset
                else:
                    return queryset
            return queryset.order_by(*ordering)
        return queryset


class PrizeEndpoint(AscribeModelViewSet):
    queryset = Prize.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    json_name = 'prizes'

    def retrieve(self, request, pk=None, *args, **kwargs):
        if not pk.isdigit():
            self.kwargs['pk'] = Prize.objects.get(whitelabel_settings__subdomain=pk).pk
        return super(PrizeEndpoint, self).retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        prize = serializer.save()
        PrizeUser.objects.create(prize=prize, user=self.request.user)

    def perform_update(self, serializer):
        # TODO consider putting this logic in .save() method of Prize model
        # instead
        old_prize = self.get_object()
        new_prize = serializer.save()
        # TODO verify what is needed:
        #   1. deactivate judges only
        #   2. jury members only
        #   3. both as done in uncommented code
        #   4. increment the prizepiece rounds upon is_selected
        #   5. reset the is_selected field
        # prize.prizeuser_set.filter(is_judge=True).update(is_judge=False)
        # prize.prizeuser_set.filter(is_jury=True).update(is_jury=False)
        if old_prize.active_round != new_prize.active_round:
            new_prize.prizeuser_set.filter(
                Q(is_judge=True) | Q(is_jury=True),
            ).update(
                is_judge=False,
                is_jury=False,
            )
            for prizepiece in PrizePiece.objects.filter(prize_id=new_prize.id):
                if prizepiece.is_selected:
                    prizepiece.round += 1
                    prizepiece.is_selected = False
                    prizepiece.save()
            # TODO send email(s) ?

    def get_serializer_class(self):
        return PrizeSerializer


class PrizeUserEndpoint(UserEndpoint):
    """
    Register user to the prize
    """
    queryset = PrizeUser.objects.all()
    permission_classes = [IsAuthenticatedOrSignUpOnly]
    json_name = 'users'

    def list(self, request, domain_pk=None):
        queryset = PrizeUser.objects.filter(user__in=self.get_queryset(),
                                            prize__whitelabel_settings__subdomain=domain_pk)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def create(self, request, domain_pk=None):
        request.data['prize_name'] = domain_pk
        serializer = WebUserSerializer(data=request.data)
        if serializer.is_valid():
            response = super(PrizeUserEndpoint, self).create(request)

            prize = Prize.objects.get(whitelabel_settings__subdomain=domain_pk)
            user = User.objects.get(email=serializer.validated_data['email'])
            try:
                PrizeUser.objects.get(prize=prize, user=user)
            except ObjectDoesNotExist:
                prize_user = PrizeUser.objects.create(prize=prize, user=user)
                prize_user.save()
            return response
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def login(self, request, domain_pk=None):
        response = super(PrizeUserEndpoint, self).login(request)
        if response.data['success']:
            prize = Prize.objects.get(whitelabel_settings__subdomain=domain_pk)
            try:
                PrizeUser.objects.get(prize=prize, user__email=request.data['email'].lower())
            except ObjectDoesNotExist:
                user = User.objects.get(email=request.data['email'].lower())
                PrizeUser.objects.create(prize=prize, user=user)
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return response

    def get_serializer_class(self):
        if self.action == 'list':
            return WebPrizeUserSerializer
        return WebUserSerializer


class PrizeJuryEndpoint(UserEndpoint):
    """
    Register user to the prize
    """
    queryset = PrizeUser.objects.filter(is_jury=True, datetime_deleted=None)
    permission_classes = [IsAuthenticatedAndAdmin]
    json_name = 'members'

    def list(self, request, domain_pk=None):
        self.action = 'jury-list'
        return super(PrizeJuryEndpoint, self).list(request)

    def create(self, request, domain_pk=None):
        self.action = 'jury-create'
        request.data['prize_name'] = domain_pk
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            # make a user jury member or sign him up as a user and make him a jury member
            user = createOrGetUser(data['email'])
            prize = Prize.objects.get(whitelabel_settings__subdomain=domain_pk)
            try:
                prize_user = PrizeUser.objects.filter(prize=prize, user=user)
                if not prize_user:
                    prize_user = PrizeUser.objects.create(prize=prize, user=user)
                else:
                    prize_user = prize_user[0]

                prize_user.is_jury = True
                prize_user.save()
                msg = u'You have successfully invited "{}" as a jury member to {} prize.' \
                    .format(data['email'], prize.name)
                try:
                    UserNeedsToRegisterRole.objects.get(user=user, type="UserNeedsToRegisterRole")
                    validate_role = UserValidateEmailRole.create(user=user)
                    validate_role.save()
                    email_signup_judge.apply_async((user, validate_role.token, domain_pk))
                    # this needs to send a custom email as well as a signup email
                except ObjectDoesNotExist:
                    # this needs to send a custom email
                    email_invite_judge.apply_async((user, domain_pk))
                return Response({'success': True, 'notification': msg}, status=status.HTTP_201_CREATED)

            except IntegrityError as e:
                msg = u'"{}" can not be added as a jury member to {} prize.'.format(data['email'], prize.name)
                return Response({'success': False, 'errors': {'email': [msg]}}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, domain_pk=None):
        self.action = 'jury-delete'
        data = {'email': pk, 'prize_name': domain_pk}
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            jury = serializer.validated_data['jury']
            jury.delete_safe()
            msg = u'You have succesfully deleted {} from the jury list'.format(data['email'])
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticatedAndAdmin])
    def activate(self, request, pk=None, domain_pk=None):
        data = {'email': pk, 'prize_name': domain_pk}
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            jury = serializer.validated_data['jury']
            jury.datetime_deleted = None
            jury.save()
            msg = u'You have succesfully activated jury {}'.format(data['email'])
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticatedAndAdmin])
    def resend(self, request, pk=None, domain_pk=None):
        data = {'email': pk, 'prize_name': domain_pk}
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            jury = serializer.validated_data['jury']
            email_invite_judge.apply_async((jury.user, 'sluice'))
            msg = u'You have succesfully activated jury {}'.format(data['email'])
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == 'jury-list':
            return WebPrizeJurySerializer
        if self.action == 'jury-create':
            return PrizeJuryForm
        if self.action in ['jury-delete', 'activate', 'resend']:
            return PrizeJuryActionForm
        return WebPrizeJurySerializer

    def get_queryset(self):
        try:
            prize = Prize.objects.get(whitelabel_settings__subdomain=self.kwargs['domain_pk'])
            return PrizeUser.objects.filter(prize=prize, is_jury=True).select_related('user')
        except:
            return PrizeUser.objects.none()


class PrizePieceEndpoint(PieceEndpoint):
    """
    Prize Piece endpoint
    """
    filter_backends = (filters.SearchFilter, RatingOrdeningFilter,)
    ordering_fields = ('title', 'note_at_piece', 'artist_name', 'selected')
    ordering = ('note_at_piece',)

    def list(self, request, domain_pk=None):
        unfiltered_count = len(PrizePieceEndpoint.get_list_queryset(domain_pk, self.request.user))
        return super(PrizePieceEndpoint, self).list(request, unfiltered_count=unfiltered_count)

    def retrieve(self, request, pk=None, domain_pk=None):
        return super(PrizePieceEndpoint, self).retrieve(request, pk)

    def create(self, request, domain_pk=None):
        self.action = 'prize-create'
        request.data['prize_name'] = domain_pk
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.action = 'create'
            response = super(PrizePieceEndpoint, self).create(request)
            try:
                piece_id = response.data['piece']['id']
            except:
                return Response({'success': False, 'errors': 'Cannot reach piece'}, status=status.HTTP_404_NOT_FOUND)
            piece = Piece.objects.get(id=piece_id)
            prize = serializer.validated_data['prize_name']
            extra_data = serializer.get_extra_data(request.data)
            return PrizePieceEndpoint._submit_to_prize(request, prize, piece, extra_data)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None, domain_pk=None):
        request.data['prize_name'] = domain_pk
        request.data['id'] = pk
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            piece = serializer.validated_data['id']
            prize = serializer.validated_data['prize_name']
            extra_data = serializer.get_extra_data(request.data)
            return PrizePieceEndpoint._submit_to_prize(request, prize, piece, extra_data)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _submit_to_prize(request, prize, piece, extra_data):
        prize_piece = PrizePiece.objects.create(user=request.user, piece=piece, prize=prize, extra_data=extra_data)
        prize_piece.save()
        remaining = prize.num_submissions - len(PrizePiece.objects.filter(prize=prize, user=request.user))
        acl = ActionControl.objects.get(user=request.user, piece=piece, edition=None)
        acl.acl_delete = False
        acl.save()
        msg = u'You have successfully submitted "{}" to {}, {} submissions remaining.' \
            .format(piece.title,
                    prize.name,
                    remaining)
        subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
            'HTTP_ORIGIN') else 'www'
        email_submit_prize.delay(request.user, piece, subdomain)
        return Response({'success': True,
                         'notification': msg,
                         'piece': WebPrizeBasicPieceSerializer(piece, context={'request': request}).data},
                        status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action == 'prize-create':
            return WebPrizePieceForm
        if self.action == 'create':
            return PieceForm
        if self.action == 'submit':
            return PrizePieceSubmitForm
        if self.action == 'list':
            return WebPrizeBasicPieceSerializer
        return WebPrizePieceSerializer

    def get_queryset(self):
        if self.action in ['list']:
            return PrizePieceEndpoint.get_list_queryset(self.kwargs['domain_pk'],
                                                        self.request.user)
        return super(PrizePieceEndpoint, self).get_queryset()

    @staticmethod
    def get_list_queryset(prize_name, user):
        if user == AnonymousUser():
            return Piece.objects.none()
        prize = Prize.objects.get(whitelabel_settings__subdomain=prize_name)
        try:
            prize_user = PrizeUser.objects.get(prize=prize, user=user, datetime_deleted=None)
        except PrizeUser.DoesNotExist:
            return PieceEndpoint.get_list_queryset(user)

        if prize_user and (prize_user.is_admin or prize_user.is_jury or prize_user.is_judge):
            prize_pieces = PrizePiece.objects.filter(prize=prize, round=prize.active_round).select_related('piece')
            return Piece.objects.filter(id__in=[p.piece.id for p in prize_pieces])
        return Piece.objects.none()


class RatingEndpoint(NoteEndpoint):
    """
    Rating API Endpoint
    """
    queryset = Rating.objects.all()
    permission_classes = [IsAuthenticatedAndJury]

    json_name = 'ratings'

    def list(self, request, domain_pk=None):
        return super(RatingEndpoint, self).list(request)

    def retrieve(self, request, pk=None, domain_pk=None):
        queryset = self.get_queryset()
        try:
            rating = queryset.get(user=request.user, piece_id=pk)
        except ObjectDoesNotExist:
            rating = None

        if rating:
            serializer = self.get_serializer(rating)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    @detail_route(methods=['get'], permission_classes=[IsAuthenticatedAndJury])
    def average(self, request, pk=None, domain_pk=None):
        ratings = self.get_queryset()
        serializer = self.get_serializer(ratings, context={'request': request})
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, domain_pk=None):
        serializer = self.get_serializer(data=request.data)
        queryset = self.get_queryset()

        if serializer.is_valid():
            piece = serializer.validated_data['piece_id']
            try:
                db_note = queryset.get(user=request.user, piece=piece)
                db_note.note = serializer.validated_data['note']
                db_note.save()
            except ObjectDoesNotExist:
                db_note = queryset.create(user=request.user,
                                          edition=None,
                                          piece=piece,
                                          note=serializer.validated_data['note'],
                                          type=queryset.model.__name__)
                db_note.save()
            prize = Prize.objects.get(whitelabel_settings__subdomain=self.kwargs['domain_pk'])
            prize_piece = PrizePiece.objects.get(piece=piece, prize=prize)
            prize_piece.set_average()
            self.action = 'list'
            serializer = self.get_serializer(db_note)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticatedAndJury])
    def select(self, request, pk=None, domain_pk=None):
        data = {}
        data['prize_name'] = domain_pk
        data['id'] = pk
        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            piece = serializer.validated_data['id']
            prize_piece = PrizePiece.objects.get(piece=piece)
            prize_piece.is_selected = not prize_piece.is_selected
            prize_piece.save()

            msg = u'You have {}shortlisted "{}"'.format('' if prize_piece.is_selected else 'un', piece.title)
            self.action = 'average'
            serializer = self.get_serializer(self.get_queryset(), context={'request': request})
            return Response({'success': True, 'notification': msg,
                             'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        filter_kwargs = {}
        subdomain = self.kwargs['domain_pk']
        prize_round = self.request.query_params.get('prize_round')

        # TODO HACK ALERT! Will be changed asap.
        if prize_round is not None and subdomain == 'portfolioreview':
            round_two_starttime = datetime.strptime(
                settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
                settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
            ).replace(tzinfo=pytz.UTC)
            if prize_round == '1':
                filter_kwargs['datetime__lt'] = round_two_starttime
            elif prize_round == '2':
                filter_kwargs['datetime__gte'] = round_two_starttime

        if self.action in ['list']:
            prize = Prize.objects.get(whitelabel_settings__subdomain=subdomain)
            prize_pieces = PrizePiece.objects.filter(prize=prize).select_related('piece')
            filter_kwargs.update(
                piece_id__in=[p.piece.id for p in prize_pieces],
                user=self.request.user,
            )
        elif self.action == 'average':
            filter_kwargs['piece_id'] = self.kwargs['pk']

        return Rating.objects.filter(**filter_kwargs)

    def get_serializer_class(self):
        if self.action == 'create':
            return NoteSerializer
        elif self.action == 'average':
            return RatingAverageSerializer
        if self.action == 'select':
            return RatingSelectSerializer
        return RatingSerializer


class PrizeNoteEndpoint(RatingEndpoint):
    """
    Prize Note API Endpoint
    """
    queryset = PrivateNote.objects.all()
    permission_classes = [IsAuthenticatedAndJury]
    json_name = 'notes'

    def get_queryset(self):
        if self.action in ['list']:
            prize = Prize.objects.get(whitelabel_settings__subdomain=self.kwargs['domain_pk'])
            prize_pieces = PrizePiece.objects.filter(prize=prize).select_related('piece')
            return PrivateNote.objects.filter(piece_id__in=[p.piece.id for p in prize_pieces], user=self.request.user)
        return PrivateNote.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return NoteSerializer
        return PrizeNoteSerializer
