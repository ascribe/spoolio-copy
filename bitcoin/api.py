from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from oauth2_provider.ext.rest_framework.authentication import OAuth2Authentication

from bitcoin.tasks import transaction_monitor


class BitcoinNewBlockEndpoint(APIView):
    """
    API endpoint for the blocktrail webhook

    This endpoint will receive a post from blocktrail every time
    a subscribed transaction is confirmed.
    """
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # check transaction events
        if request.data['event_type'] == 'transaction':
            transaction_monitor.delay(request.data['data']['hash'], request.data['data']['confirmations'])
        return Response({'success': True}, status=status.HTTP_200_OK)

