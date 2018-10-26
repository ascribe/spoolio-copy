from __future__ import absolute_import
from rest_framework.test import APIRequestFactory, force_authenticate
from prize.api import PrizeEndpoint


class APIUtilPrize(object):
    factory = APIRequestFactory()

    def create_prize(self, user, whitelabel, num_submissions=1, rounds=1):
        data = {'whitelabel_settings': whitelabel.pk,
                'num_submissions': num_submissions,
                'rounds': rounds}

        view = PrizeEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/prizes/', data)
        force_authenticate(request, user=user)

        response = view(request)
        return response
