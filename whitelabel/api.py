from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status, viewsets

from whitelabel.models import WhitelabelSettings
from whitelabel.serializers import WhitelabelMarketplaceSerializer
from web.api_util import GenericViewSetKpi


class WhitelabelSettingsEndpoint(GenericViewSetKpi):
    """
    Whitelabel Marketplace API endpoint
    """
    queryset = WhitelabelSettings.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    json_name = 'whitelabels'

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()

        try:
            settings = queryset.get(subdomain=pk)
        except ObjectDoesNotExist:
            settings = None

        if settings:
            serializer = self.get_serializer(settings)
            return Response({'success': True, self.json_name[:-1]: serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response({'success': False},
                            status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        return WhitelabelMarketplaceSerializer

    def get_queryset(self):
        if self.action == 'list':
            return WhitelabelSettings.objects.filter(user=self.request.user)
        return WhitelabelSettings.objects.all()
