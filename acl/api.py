from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from web.api_util import GenericViewSetKpi
from acl.models import ActionControl
from acl.serializers import ActionControlSerializer


class ActionControlEndpoint(GenericViewSetKpi):
    """
    ActionControl API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = ActionControl.objects.all()
    permission_classes = [AllowAny]
    json_name = 'acls'

    def list(self, request):
        queryset = ActionControl.objects.filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)

        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return ActionControlSerializer

    def get_queryset(self):
        return self.queryset.filter(organization='ascribe')
