from rest_framework import status
from rest_framework.response import Response

from acl.models import ActionControl
from notifications.models import PieceNotification, EditionNotification, ContractAgreementNotification
from notifications.serializers import PieceNotificationSerializer, EditionNotificationSerializer, \
    ContractAgreementNotificationSerializer
from ownership.models import ContractAgreement
from piece.models import Piece, Edition
from util.util import extract_subdomain

from web.api_util import GenericViewSetKpi
from whitelabel.models import WhitelabelSettings


class PieceNotificationEndpoint(GenericViewSetKpi):
    """
    Piece Notification API endpoint
    """
    queryset = Piece.objects.all()
    serializer_class = PieceNotificationSerializer

    def list(self, request, classname='piece'):
        """
        Retrieve the request actions of the pieces
        """
        notifications = []
        for item in ActionControl.get_items_for_user(self.request.user, classname=classname):
            notification = self.get_notification_class().get_notifications(item, self.request.user)
            if notification:
                notifications.append(self.get_notification_class()(notification, item))
        serializer = self.get_serializer(notifications, many=True)

        return Response({'success': True,
                         'notifications': serializer.data},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            piece = Piece.objects.get(id=pk)
        except Piece.DoesNotExist:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        notification = self.get_notification_class().get_notifications(piece, request.user)

        try:
            assert len(notification) > 0
        except AssertionError:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(self.get_notification_class()(notification, piece))

        return Response({'success': True, 'notification': serializer.data},
                        status=status.HTTP_200_OK)

    def get_notification_class(self):
        return PieceNotification


class EditionNotificationEndpoint(PieceNotificationEndpoint):
    """
    Edition Notification API endpoint
    """
    queryset = Edition.objects.all()
    serializer_class = EditionNotificationSerializer

    def list(self, request, classname='edition'):
        return super(EditionNotificationEndpoint, self).list(request, classname)

    def retrieve(self, request, pk=None):
        try:
            edition = Edition.objects.get(bitcoin_path__contains=pk)
        except Edition.DoesNotExist:
            # TODO Log something perhaps
            # TODO Possibly, return more informative message, e.g.:
            # {'success': False, 'reason': 'Edition {} not found.'.format(pk)}
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        notification = self.get_notification_class().get_notifications(edition, request.user)

        try:
            assert len(notification) > 0
        except AssertionError:
            # TODO Log something perhaps
            # TODO Possibly, return more informative message, e.g.:
            # {'success': False, 'reason': 'Edition {} has no notifications'.format(pk)}
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(self.get_notification_class()(notification, edition))
        return Response({'success': True, 'notification': serializer.data},
                        status=status.HTTP_200_OK)

    def get_notification_class(self):
        return EditionNotification


class ContractAgreementNotificationEndpoint(GenericViewSetKpi):
    """
    ContractAgreement Notification API endpoint
    """
    queryset = ContractAgreement.objects.all()
    serializer_class = ContractAgreementNotificationSerializer

    def list(self, request):
        """
        Retrieve the request actions of the pieces
        """
        notifications = []
        for item in self.get_queryset():
            notification = ContractAgreementNotification.get_notifications(item, self.request.user)
            if notification:
                notifications += [ContractAgreementNotification(notification, item)]
        serializer = self.get_serializer(notifications, many=True)

        return Response({'success': True,
                         'notifications': serializer.data},
                        status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = ContractAgreement.objects.filter(signee=self.request.user,
                                                    contract__is_public=False).pending()
        subdomain = extract_subdomain(self.request.META['HTTP_ORIGIN']) if self.request.META.has_key('HTTP_ORIGIN') else 'www'
        try:
            issuer = WhitelabelSettings.objects.get(subdomain=subdomain).user
        except WhitelabelSettings.DoesNotExist:
            return queryset
        return queryset.filter(contract__issuer=issuer)

