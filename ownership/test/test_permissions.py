"""
Custom Permission tests
"""

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from ownership.api import TransferEndpoint


# unauthenticated user can only access detail view
# authenticated user can access all views
class TransferIsAuthenticatedOrReadOnlyTest(TestCase):
    ACTIONS_GET = ['list', 'retrieve']
    ACTIONS_POST = ['create']

    @classmethod
    def setUpClass(cls):
        super(TransferIsAuthenticatedOrReadOnlyTest, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(email='test@test.com',
                                            username='test@test.com',
                                            password='1234567890')

    def testUnauthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/ownership/transfers/')
        for action in self.ACTIONS_GET:
            view = TransferEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/ownership/transfers/', {})
        for action in self.ACTIONS_POST:
            view = TransferEndpoint.as_view({'post': action})
            response = view(request)
            self.assertIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

    def testAuthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/ownership/transfers/')
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_GET:
            view = TransferEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/ownership/transfers/', {'key':''})
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_POST:
            view = TransferEndpoint.as_view({'post': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])



