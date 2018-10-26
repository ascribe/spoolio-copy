from rest_framework import filters
from piece.api import PieceEndpoint
from users.api import UserEndpoint
from whitelabel.cyland.filters import CylandSubmittedPieceFilter
from whitelabel.cyland.serializers import CylandBasicPieceSerializer, CylandPieceExtraDataForm, CylandUserSerializer, \
    CylandPieceSerializer


class CylandUserEndpoint(UserEndpoint):
    """
    IkonoTV User endpoint
    """
    def get_serializer_class(self):
        if self.action == 'list':
            return CylandUserSerializer
        return super(CylandUserEndpoint, self).get_serializer_class()


class CylandPieceEndpoint(PieceEndpoint):
    """
    Cyland Piece endpoint
    """

    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = CylandSubmittedPieceFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return CylandBasicPieceSerializer
        if self.action == 'retrieve':
            return CylandPieceSerializer
        if self.action == 'extradata':
            return CylandPieceExtraDataForm
        return super(CylandPieceEndpoint, self).get_serializer_class()