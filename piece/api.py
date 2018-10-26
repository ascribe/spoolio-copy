import os
from urllib2 import URLError

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from rest_framework import status, filters

from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from blobs.models import DigitalWork, File, Thumbnail
from piece.models import PieceFactory, Piece, Edition
from piece.serializers import PieceSerializer, PieceDeleteForm, BasicEditionSerializer, \
    BasicPieceSerializerWithFirstEdition, PieceForm, PieceExtraDataForm, EditionDeleteForm, EditionRegister, \
    DetailedEditionSerializer
from piece.tasks import register_editions, handle_edition_creation_error
from web.api_util import PaginatedGenericViewSetKpi
from ownership.models import OwnershipEditions
from acl.models import ActionControl


class AclFilterView(object):
    search_fields_acl = ('acl_transfer', 'acl_consign', 'acl_share', 'acl_loan', 'acl_create_editions')

    def get_acl_filter(self):
        acl_filter_keys = set(self.request.query_params.keys()) & set(self.search_fields_acl)
        return {k: self.request.query_params[k] for k in acl_filter_keys}


class PieceEndpoint(PaginatedGenericViewSetKpi, AclFilterView):
    """
    Piece API endpoint
    """
    queryset = Piece.objects.all()

    permission_classes = (IsAuthenticatedOrReadOnly,)

    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('title', 'artist_name')

    ordering_fields = ('title', 'artist_name', 'date_created', 'datetime_registered')
    ordering = ('artist_name',)

    json_name = 'pieces'

    def list(self, request, *args, **kwargs):
        unfiltered_count = kwargs.pop('unfiltered_count',
                                      len(PieceEndpoint.get_list_queryset(self.request.user)))
        return super(PieceEndpoint, self).list(request,  unfiltered_count=unfiltered_count, *args, **kwargs)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        pk = unicode(pk)
        try:
            if pk.isdigit():
                # database ID
                piece = queryset.get(id=pk)
            else:
                # bitcoin ID
                piece = queryset.get(bitcoin_path__regex=r'^\S+?:{}$'.format(pk))
        except (Piece.DoesNotExist, ValueError):
            piece = None

        if piece:
            serializer = self.get_serializer(piece)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        if 'file_url' in request.data:
            request.data['digital_work_key'] = request.data['file_url']
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            # TODO: this might be a slow, create shallow files first and generate content later?
            try:
                data = PieceEndpoint._createFiles(request, data)
            except (ValueError, URLError) as e:
                return Response({'success': False,
                                 'errors': [e.message]})
            piece = PieceFactory.register(data, request.user)

            msg = u'You have successfully registered "%s" by %s.' % (data['title'],data['artist_name'])
            return Response({'success': True,
                             'notification': msg,
                             'piece': PieceSerializer(piece, context={'request': request}).data
                             },
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete the piece from our DB using datetime_deleted

        :param request: HttpRequest: AJAX POST
        :return: None
        """
        data = request.data.copy()
        data['id'] = pk
        serializer = PieceDeleteForm(data=data, context={'request': request})
        if serializer.is_valid():
            piece = serializer.validated_data['id']
            piece.delete_safe()
            acl = ActionControl.objects.get(user=request.user, piece=piece, edition=None)
            acl.acl_view = False
            acl.save()
            msg = u'You have successfully deleted "%s" by %s.' % (piece.title, piece.artist_name)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'], permission_classes=[IsAuthenticated], url_path='editions')
    def editions(self, request, pk=None):
        try:
            queryset = ActionControl.get_items_for_user(self.request.user,
                                                        self.get_acl_filter(),
                                                        classname='edition')\
                .filter(parent_id=pk)\
                .order_by("edition_number")
        except ValueError:
            # empty queryset
            queryset = Edition.objects.none()

        if not len(queryset):
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.paginator.get_paginated_response(serializer.data, name='editions')

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({'success': True, 'editions': serializer.data}, status=status.HTTP_200_OK)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def extradata(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # bitcoin_id returns the parent of the edition in this serializer
            piece = serializer.validated_data['piece_id']
            extra_data = piece.extra_data
            for k, v in serializer.validated_data['extradata'].iteritems():
                extra_data[k] = v
            piece.extra_data = extra_data
            piece.save()
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _createFiles(request, data):
        if hasattr(request.auth, 'token'):
            # API User: needs to generate digital work first from url
            url = data['digital_work_key']
            filename = os.path.split(url)[1]
            key = File.create_key("/".join([filename, "digitalwork"]), filename, request.user)
            digital_work = DigitalWork(user=request.user, digital_work_file=key)
            digital_work.save()
            digital_work.upload(url)
        else:
            # WEB User: file created by fineuploader
            digital_work = DigitalWork.objects.filter(user=request.user,
                                                      digital_work_file=data['digital_work_key']).order_by('-id')[0]
        if 'thumbnail_file' in data and data['thumbnail_file']:
            # Thumbnail already provided
            thumbnail = data['thumbnail_file']
        else:
            # Create thumbnail from digital_work
            thumbnail = digital_work.create_thumbnail()

        if thumbnail is None:
            # Thumbnail fallback
            thumbnail = Thumbnail(user=request.user, thumbnail_file=settings.THUMBNAIL_DEFAULT)
            thumbnail.save()

        data['digital_work'] = digital_work
        data['thumbnail'] = thumbnail
        return data

    def get_serializer_class(self):
        if self.action == 'list':
            return BasicPieceSerializerWithFirstEdition
        if self.action == 'create':
            return PieceForm
        if self.action == 'extradata':
            return PieceExtraDataForm
        if self.action == 'editions':
            return BasicEditionSerializer
        return PieceSerializer

    def get_queryset(self):
        if self.action in ['list']:
            return PieceEndpoint.get_list_queryset(self.request.user, acl_filter=self.get_acl_filter())
        return self.queryset

    @staticmethod
    def get_list_queryset(user, acl_filter={}):
        if user == AnonymousUser():
            return Piece.objects.none()
        return ActionControl.get_items_for_user(user, acl_filter=acl_filter)


class EditionEndpoint(PaginatedGenericViewSetKpi, AclFilterView):
    """
    Edition API endpoint
    """
    queryset = Edition.objects.all()

    # authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('edition_number',)
    ordering_fields = ('edition_number',)

    json_name = 'editions'

    def create(self, request):
        """
        Register the number of editions and create editions on the database
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            piece = serializer.validated_data['piece_id']
            num_editions = serializer.validated_data['num_editions']

            register_editions(piece, piece.user_registered, num_editions).delay(link_error=handle_edition_creation_error.s())

            msg = u'You successfully registered {} editions for piece with ID {}.'.format(num_editions,
                                                                                          piece.bitcoin_id)
            return Response({'success': True,
                             'notification': msg},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()

        try:
            if pk.isdigit():
                # database ID
                edition = queryset.get(id=pk)
            else:
                # bitcoin ID
                edition = queryset.get(bitcoin_path__contains=pk)
        except (Edition.DoesNotExist, Edition.MultipleObjectsReturned):
            edition = None

        if edition:
            serializer = self.get_serializer(edition)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """
        Delete the piece from our DB using datetime_deleted

        :param request: HttpRequest: AJAX POST
        :return: None
        """
        data = request.data.copy()
        data['bitcoin_id'] = pk
        serializer = EditionDeleteForm(data=data, context={'request': request})
        if serializer.is_valid():
            editions = serializer.validated_data['bitcoin_id']
            for edition in editions:
                edition.delete_safe()
                acl = ActionControl.objects.get(user=request.user, piece=edition.parent, edition=edition)
                acl.acl_view = False
                acl.save()

            msg = u'You have successfully deleted %d editions.' % (len(editions))
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == 'list':
            return BasicEditionSerializer
        elif self.action == 'create':
            return EditionRegister
        return DetailedEditionSerializer

    def get_queryset(self):
        if self.action in ['list']:
            if self.request.user == AnonymousUser():
                return self.queryset.none()
            return ActionControl.get_items_for_user(self.request.user,
                                                    acl_filter=self.get_acl_filter(),
                                                    classname='edition')
        return Edition.objects.filter(datetime_deleted=None)
