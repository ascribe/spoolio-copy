from rest_framework.test import APIRequestFactory, force_authenticate
from webhooks.api import HookViewSet


class APIUtilWebhook(object):
    factory = APIRequestFactory()

    def create_webhook(self, user, event, target):

        data = {
            'event': event,
            'target': target,
            'user': user
        }

        view = HookViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/transfers/', data)
        force_authenticate(request, user=user)

        return view(request)
