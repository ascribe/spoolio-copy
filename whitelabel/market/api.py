from rest_framework import filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from ownership.api import ConsignEndpoint

from piece.api import PieceEndpoint, EditionEndpoint
from users.api import UserEndpoint
from whitelabel.market.serializers import MarketUserSerializer, MarketBasicPieceSerializer, MarketPieceSerializer, \
    MarketSerializer, MarketPieceExtraDataForm, MarketDetailedEditionSerializer, MarketBasicEditionSerializer
from whitelabel.models import WhitelabelSettings


class MarketEndpoint(ModelViewSet):
    queryset = WhitelabelSettings.objects.all()
    serializer_class = MarketSerializer


class MarketUserEndpoint(UserEndpoint):
    """
    Market User endpoint
    """
    def list(self, request, domain_pk=None):
        return super(MarketUserEndpoint, self).list(request)

    def retrieve(self, request, pk=None, domain_pk=None):
        return super(MarketUserEndpoint, self).retrieve(request, pk)

    def create(self, request, domain_pk=None):
        return super(MarketUserEndpoint, self).create(request)

    def get_serializer_class(self):
        if self.action == 'list':
            return MarketUserSerializer
        return super(MarketUserEndpoint, self).get_serializer_class()


class MarketPieceEndpoint(PieceEndpoint):
    """
    Market Piece endpoint
    """
    filter_backends = (filters.SearchFilter,
                       filters.DjangoFilterBackend,
                       filters.OrderingFilter,)

    def list(self, request, domain_pk=None, *args, **kwargs):
        return super(MarketPieceEndpoint, self).list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, domain_pk=None):
        return super(MarketPieceEndpoint, self).retrieve(request, pk)

    def create(self, request, domain_pk=None):
        return super(MarketPieceEndpoint, self).create(request)

    def delete(self, request, pk=None, domain_pk=None):
        return super(MarketPieceEndpoint, self).delete(request, pk)

    @detail_route(methods=['get'], permission_classes=[IsAuthenticated], url_path='editions')
    def editions(self, request, pk=None, domain_pk=None):
        return super(MarketPieceEndpoint, self).editions(request, pk)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def extradata(self, request, pk=None, domain_pk=None):
        return super(MarketPieceEndpoint, self).extradata(request, pk)

    def get_serializer_class(self):
        if self.action == 'list':
            return MarketBasicPieceSerializer
        if self.action == 'retrieve':
            return MarketPieceSerializer
        if self.action == 'extradata':
            return MarketPieceExtraDataForm
        if self.action == 'editions':
            return MarketDetailedEditionSerializer
        return super(MarketPieceEndpoint, self).get_serializer_class()


class MarketEditionEndpoint(EditionEndpoint):
    """
    Market Edition endpoint
    """
    def list(self, request, domain_pk=None, *args, **kwargs):
        return super(MarketEditionEndpoint, self).list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, domain_pk=None):
        return super(MarketEditionEndpoint, self).retrieve(request, pk)

    def create(self, request, domain_pk=None):
        return super(MarketEditionEndpoint, self).create(request)

    def delete(self, request, pk=None, domain_pk=None):
        return super(MarketEditionEndpoint, self).delete(request, pk)

    def get_serializer_class(self):
        if self.action == 'list':
            return MarketBasicEditionSerializer
        if self.action == 'retrieve':
            return MarketDetailedEditionSerializer
        return super(MarketEditionEndpoint, self).get_serializer_class()


class MarketConsignEndpoint(ConsignEndpoint):

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request):
        # TODO: (@Troy) Upon confirm of the consignment, the edition needs to be added to the marketplace (i.e. shopify)
        # there are multiple ways to proceed:
        # - use the shopify API here
        # - create share here to lumenussupport@ascribe.io and do it manually
        # -
        # Make sure to use celery tasks if the call is blocking!
        return super(MarketConsignEndpoint, self).confirm(request)
