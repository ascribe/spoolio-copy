from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework.authtoken.models import Token
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from oauth2_provider.models import AccessToken, get_application_model

from web.api_util import GenericViewSetKpi

from serializers import ApplicationSerializer, ApplicationForm, ApplicationTokenRefreshForm

Application = get_application_model()


class ApplicationEndpoint(GenericViewSetKpi):
    """
    OAuth User API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = Application.objects.all()
    permission_classes = [IsAuthenticated]
    json_name = 'applications'

    def list(self, request, pk=None):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()

        try:
            application = queryset.get(pk=pk)
        except ObjectDoesNotExist:
            application = None

        if application:
            serializer = self.get_serializer(application)
            return Response({'success': True, self.json_name[:-1]: serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            app = Application(name=data['name'], redirect_uris="", user=request.user,
                              client_type=Application.CLIENT_CONFIDENTIAL,
                              authorization_grant_type=Application.GRANT_PASSWORD)
            app.save()
            create_token(app)
            self.action = 'retrieve'
            serializer = self.get_serializer(app)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def refresh_token(self, request):
        self.action = 'refresh_token'
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            app = data['name']
            token = AccessToken.objects.get(application=app)
            token.delete()
            create_token(app)
            self.action = 'list'
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({'success': True, self.json_name: serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationForm
        if self.action == 'refresh_token':
            return ApplicationTokenRefreshForm
        return ApplicationSerializer

    def get_queryset(self):
        if self.request.user == AnonymousUser():
            return self.queryset.none()
        if self.action in ["list", "retrieve"]:
            return self.queryset.filter(user=self.request.user)
        return self.queryset


def create_token(application, token='', valid_days=1000, scope='read write'):
    expires = timezone.now() + timedelta(days=valid_days)

    if not token or not isinstance(token, basestring):
        token = Token.generate_key(Token(application.user.username))

    return AccessToken.objects.create(user=application.user, token=token,
                                      application=application,
                                      expires=expires,
                                      scope=scope)
