"""
Custom Permission tests
"""

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from piece.api import PieceEndpoint


# unauthenticated user can only access detail view
# authenticated user can access all views
class PieceIsAuthenticatedOrReadOnlyTest(TestCase):
    ACTIONS_GET = ['list', 'retrieve']
    ACTIONS_POST = ['create']

    @classmethod
    def setUpClass(cls):
        super(PieceIsAuthenticatedOrReadOnlyTest, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(email='test@test.com',
                                            username='test@test.com',
                                            password='1234567890')

    def testUnauthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/pieces/')
        for action in self.ACTIONS_GET:
            view = PieceEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/pieces/', {})
        for action in self.ACTIONS_POST:
            view = PieceEndpoint.as_view({'post': action})
            response = view(request)
            self.assertIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

    def testAuthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/blob/digitalworks/')
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_GET:
            view = PieceEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/blob/digitalworks/', {'key':''})
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_POST:
            view = PieceEndpoint.as_view({'post': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])



