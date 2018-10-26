"""
Custom Permission tests
"""

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from blobs.api import DigitalWorkEndpoint, ThumbnailEndpoint


# authenticated user can access all views
class DigitalWorkIsAuthenticatedTest(TestCase):
    ACTIONS_GET = ['list', 'retrieve']
    ACTIONS_POST = ['create']

    @classmethod
    def setUpClass(cls):
        super(DigitalWorkIsAuthenticatedTest, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(email='test@test.com',
                                            username='test@test.com',
                                            password='1234567890')

    def testUnauthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/blob/digitalworks/')
        for action in self.ACTIONS_GET:
            view = DigitalWorkEndpoint.as_view({'get': action})
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # HTTP POST actions
        request = self.factory.post('/api/blob/digitalworks/', {})
        for action in self.ACTIONS_POST:
            view = DigitalWorkEndpoint.as_view({'post': action})
            response = view(request)
            self.assertIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

    def testAuthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/blob/digitalworks/')
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_GET:
            view = DigitalWorkEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])

        # HTTP POST actions
        request = self.factory.post('/api/blob/digitalworks/', {'key':''})
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_POST:
            view = DigitalWorkEndpoint.as_view({'post': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])


class ThumbailIsAuthenticatedTest(TestCase):
    ACTIONS_GET = ['list', 'retrieve']
    ACTIONS_POST = ['create']

    @classmethod
    def setUpClass(cls):
        super(ThumbailIsAuthenticatedTest, cls).setUpClass()
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(email='test@test.com',
                                            username='test@test.com',
                                            password='1234567890')

    def testUnauthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/blob/thumbnails/')
        for action in self.ACTIONS_GET:
            view = ThumbnailEndpoint.as_view({'get': action})
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testAuthenticatedUser(self):
        # HTTP GET actions
        request = self.factory.get('/api/blob/thumbnails/')
        force_authenticate(request, user=self.user)
        for action in self.ACTIONS_GET:
            view = ThumbnailEndpoint.as_view({'get': action})
            response = view(request)
            self.assertNotIn(response.status_code,
                             [status.HTTP_401_UNAUTHORIZED,
                              status.HTTP_403_FORBIDDEN])
