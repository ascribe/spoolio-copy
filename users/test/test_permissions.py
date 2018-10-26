"""
Custom Permission tests
"""

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from users.api import UserEndpoint


# unauthenticated user can only access create view
# authenticated user can access all views
class IsAuthenticatedOrCreateOnlyTest(TestCase):
    ACTIONS_GET = ['list', 'retrieve']
    ACTIONS_POST = ['create']

    @classmethod
    def setUpClass(cls):
        super(IsAuthenticatedOrCreateOnlyTest, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(email='test@test.com',
                                            username='test@test.com',
                                            password='1234567890')

    def testUnauthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/0.1/users/')
        for action in self.ACTIONS_GET:
            view = UserEndpoint.as_view({'get': action})
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # HTTP POST actions
        request = self.factory.post('api/0.1/users/', {})
        for action in self.ACTIONS_POST:
            view = UserEndpoint.as_view({'post': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

    def testAuthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/0.1/users/')
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_GET:
            view = UserEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/0.1/users/', {})
        for action in self.ACTIONS_POST:
            view = UserEndpoint.as_view({'post': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])
