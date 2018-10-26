from django.core.exceptions import ObjectDoesNotExist

from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from coa.forms import VerifyCoaForm
from coa.models import create, CoaFile
from coa.serializers import CoaForm, CoaSerializer
from util.crypto import import_env_key, verify
from web.api_util import GenericViewSetKpi


class CoaEndpoint(GenericViewSetKpi):
    """
    COA API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = CoaFile.objects.all()
    permission_classes = [IsAuthenticated]
    json_name = 'coas'

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        try:
            coa = queryset.get(pk=pk)
        except ObjectDoesNotExist:
            coa = None

        if coa:
            serializer = self.get_serializer(coa)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                coa = create(request.user.username, data['bitcoin_id'])
            except AssertionError, e:
                return Response({'success': False, 'errors': [e.message]},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.action = "retrieve"
            serializer = self.get_serializer(coa)
            # TODO return 201 instead of 200
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "create":
            return CoaForm
        return CoaSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def verify_coa(self, request):
        serializer = VerifyCoaForm(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            priv_key = import_env_key('COA_PRIVKEY_1')
            signature = data['signature'].replace(" ", "").replace("\r", "").replace("\n", "")
            try:
                verdict = verify(priv_key.publickey(), data['message'], signature)
                assert verdict
                return Response({'success': True, 'verdict': verdict}, status=status.HTTP_200_OK)
            except:
                return Response({'success': False,
                                 'errors': {'signature': ['Oops, the signature was invalid']}},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
