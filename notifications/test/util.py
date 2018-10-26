from __future__ import absolute_import

from rest_framework.test import APIRequestFactory, force_authenticate

from notifications.api import ContractAgreementNotificationEndpoint, PieceNotificationEndpoint, EditionNotificationEndpoint


class APIUtilEditionNotification(object):
    factory = APIRequestFactory()

    def retrieve_edition_notification(self, user, bitcoin_id):
        view = EditionNotificationEndpoint.as_view({'get': 'retrieve'})
        request = self.factory.get('/api/notifications/editions/{}/'.format(bitcoin_id))
        force_authenticate(request, user)

        response = view(request, pk=bitcoin_id)
        return response
