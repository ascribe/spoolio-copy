from rest_framework import filters
from piece.api import PieceEndpoint
from users.api import UserEndpoint
from whitelabel.ikonotv.filters import IkonotvSubmittedPieceFilter
from whitelabel.ikonotv.serializers import IkonotvBasicPieceSerializer, IkonotvPieceSerializer, IkonotvUserSerializer


class IkonotvUserEndpoint(UserEndpoint):
    """
    IkonoTV User endpoint
    """
    def get_serializer_class(self):
        if self.action == 'list':
            return IkonotvUserSerializer
        return super(IkonotvUserEndpoint, self).get_serializer_class()


class IkonotvPieceEndpoint(PieceEndpoint):
    """
    IkonoTV Piece endpoint
    """

    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = IkonotvSubmittedPieceFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return IkonotvBasicPieceSerializer
        if self.action == 'retrieve':
            return IkonotvPieceSerializer
        return super(IkonotvPieceEndpoint, self).get_serializer_class()