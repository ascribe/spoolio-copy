from django.conf import settings
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rest_hooks.models import Hook

from .serializers import HookSerializer
from web.api_util import PaginatedGenericViewset


class HookViewSet(PaginatedGenericViewset, ModelViewSet):
    """
    Retrieve, create, update or destroy webhooks.
    """
    queryset = Hook.objects.all()
    serializer_class = HookSerializer
    json_name = 'webhooks'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, pk=None, *args, **kwargs):
        response = super(HookViewSet, self).destroy(request, pk, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response({'success': True, 'id': int(pk)}, status=status.HTTP_200_OK)
        return response

    @list_route(methods=['get'], permission_classes=[AllowAny])
    def events(self, request):
        try:
            events = [e.split('.')[0] for e in settings.HOOK_EVENTS.keys()]
        except ValueError:
            # empty queryset
            events = None

        if not events:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        return Response({'success': True, 'events': events}, status=status.HTTP_200_OK)

    def get_queryset(self):
        """
        This view should return a list of all the webhooks
        for the currently authenticated user.
        """
        user = self.request.user
        return self.queryset.filter(user=user)
