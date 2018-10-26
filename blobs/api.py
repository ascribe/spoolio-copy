import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from rest_framework.decorators import list_route
from blobs.serializers import (
    FileSerializer,
    DigitalWorkSerializer,
    DigitalWorkForm,
    OtherDataForm,
    ContractBlobForm,
    ThumbnailForm,
    ThumbnailDeleteForm,
    DigitalWorkDeleteForm,
    OtherDataDeleteForm
)

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers

from blobs.models import DigitalWork, Thumbnail, OtherData
from core.api import ModelViewSetKpi
from piece.models import Piece


class FileEndpoint(ModelViewSetKpi):
    """
    File API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = None
    # When writing class based views there is no easy way to override the
    # permissions for invidual view methods. The easiest way is to
    # create custom permission classes
    permission_classes = [IsAuthenticated]
    json_name = 'files'
    key_field_name = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        queryset = self.get_queryset()

        try:
            fid = queryset.get(pk=pk, user=request.user)
        except ObjectDoesNotExist:
            fid = None

        if fid:
            serializer = self.get_serializer(fid)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        if 'key' in request.data and self.key_field_name not in request.data:
            request.data[self.key_field_name] = request.data['key']
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({'success': False, 'errors': e.detail}, status=e.status_code)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'success': True, self.json_name[:-1]: FileSerializer(serializer.instance).data}, status=status.HTTP_201_CREATED,
                        headers=headers)

    def destroy(self, request, pk=None, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data={'id': instance.id})
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({'success': False, 'errors': e.detail}, status=e.status_code)

        self.perform_destroy(instance)
        return Response({'success': True,
                         'notification': 'File deleted'}, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return FileSerializer

    def get_queryset(self):
        if self.request.user == AnonymousUser():
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)


class DigitalWorkEndpoint(FileEndpoint):
    """
    DigitalWork API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = DigitalWork.objects.all()
    json_name = 'digitalworks'
    key_field_name = 'digital_work_file'

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.digital_work_hash = instance.hash
        instance.save()

    def get_serializer_class(self):
        if self.action == 'create':
            return DigitalWorkForm
        if self.action == 'destroy':
            return DigitalWorkDeleteForm
        return DigitalWorkSerializer


class ThumbnailEndpoint(FileEndpoint):
    """
    Thumbnail API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = Thumbnail.objects.all()
    json_name = 'thumbnails'
    key_field_name = 'thumbnail_file'

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.thumbnail_sizes = {k: instance.url for k, v in settings.THUMBNAIL_SIZES.iteritems()}
        Thumbnail.thumbnail_from_url.delay(instance.url, instance.key, instance)
        instance.save()

    def get_serializer_class(self):
        if self.action == 'create':
            return ThumbnailForm
        elif self.action == 'destroy':
            return ThumbnailDeleteForm
        else:
            return FileSerializer


class OtherDataEndpoint(FileEndpoint):
    """
    OtherData API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = OtherData.objects.all()
    json_name = 'otherdatas'
    key_field_name = 'other_data_file'

    def perform_create(self, serializer):
        instance = serializer.save()
        piece = Piece.objects.get(id=serializer.initial_data['piece_id'])
        if piece:
            piece.other_data.add(instance)

    @list_route(methods=['get'], permission_classes=[AllowAny])
    def fineuploader_session(self, request):
        try:
            pk = self.request.query_params.get('pk', None).split(',')
            blobs = self.queryset.filter(id__in=pk)
            filelist = [f.fineuploader_session for f in blobs]
            return HttpResponse(json.dumps(filelist), content_type='application/json')
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            print e
        return HttpResponse(json.dumps([]), content_type='application/json')

    def get_serializer_class(self):
        if self.action == 'create':
            return OtherDataForm
        elif self.action == 'destroy':
            return OtherDataDeleteForm
        return FileSerializer


class ContractBlobEndpoint(OtherDataEndpoint):
    """
    ContractBlob API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = OtherData.objects.all()
    json_name = 'contractblobs'

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action == 'create':
            return ContractBlobForm
        elif self.action == 'destroy':
            return OtherDataDeleteForm
        return FileSerializer
