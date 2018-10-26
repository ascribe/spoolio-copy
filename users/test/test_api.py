from __future__ import absolute_import

from importlib import import_module

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from bitcoin.models import BitcoinWallet

from users.api import UserEndpoint
from users.models import (UserValidateEmailRole,
                          UserProfile,
                          UserNeedsToRegisterRole)
from users.serializers import WebUserSerializer
from users.test.util import APIUtilUsers


# Test user creation
# Test listing users
# Test retrieving users
# Test unicode validation
# Test field validation
class UsersEndpointTest(TestCase, APIUtilUsers):
    @classmethod
    def setUpClass(cls):
        super(UsersEndpointTest, cls).setUpClass()
        cls.admin_user = cls.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        cls.web_user = cls.create_user('web-user@test.com')
        cls.other_user = cls.create_user('other-user@test.com')
        cls.factory = APIRequestFactory()

    def testListWeb(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        view = UserEndpoint.as_view({'get': 'list'})
        request = self.factory.get('/api/users/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        # render the response so that we get the serialized json
        response.render()
        # get serialize the user form the db
        qs = User.objects.filter(pk=self.web_user.pk)
        serializer = WebUserSerializer(qs, many=True,
                                       context={'request': request})
        serialized_db = JSONRenderer().render({'success': True,
                                               'users': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveWeb(self):
        """
        Test that a user can only retrieve himself.
        """
        view = UserEndpoint.as_view({'get': 'retrieve'})
        url = '/api/users/{0}/'.format(self.web_user.id)
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.web_user.pk)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        response.render()
        qs = User.objects.get(pk=self.web_user.pk)
        serializer = WebUserSerializer(qs, context={'request': request})
        serialized_db = JSONRenderer().render({'success': True,
                                               'user': serializer.data})
        self.assertEqual(response.content, serialized_db)

    def testRetrieveOtherWeb(self):
        """
        Test that a user cannot retrieve other users.
        """
        view = UserEndpoint.as_view({'get': 'retrieve'})
        url = '/api/users/{0}/'.format(self.other_user.id)
        request = self.factory.get(url)
        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.other_user.pk)
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

        response.render()
        self.assertEqual(response.content, '{"success":false}')

    def testCreateWeb(self):
        """
        Test creation of a user. No authentication
        """
        test_email = 'created-user@test.com'
        view = UserEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'email': test_email,
            'password': '1234567890',
            'password_confirm': '1234567890',
            'terms': True,
        })
        request.user = AnonymousUser()

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        response.render()
        created_user = User.objects.get(email=test_email)
        serializer = WebUserSerializer(created_user)
        serialized_db = JSONRenderer().render({'success': True,
                                               'user': serializer.data})
        self.assertEqual(response.content, serialized_db)
        self.assertEqual(UserValidateEmailRole.objects.filter(user=created_user).count(), 1)
        self.assertEqual(UserProfile.objects.filter(user=created_user).count(), 1)
        self.assertEqual(UserNeedsToRegisterRole.objects.filter(user=created_user).count(), 1)
        self.assertEqual(BitcoinWallet.objects.filter(user=created_user).count(), 1)

    def test_user_email_case_insensitivity(self):
        """
        Test creating a user with an email for which there is already an
        existing user with the same email, regardless of the case.

        """
        email = 'user@test.com'
        User.objects.create(email=email)
        view = UserEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'email': email.upper(),
            'password': '1234567890',
            'password_confirm': '1234567890',
            'terms': True,
        })
        request.user = AnonymousUser()
        response = view(request)
        # check that the response is as expected
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.data), 2)
        self.assertIn('errors', response.data)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertIn('email', response.data['errors'])
        self.assertListEqual(
            response.data['errors']['email'],
            ['An account with this email/username already exists.']
        )
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        self.assertFalse(User.objects.filter(email=email.upper()).exists())

    def testActivate(self):
        """
        Test creation of a user. No authentication
        """
        test_email = 'activate-user@test.com'
        view = UserEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'email': test_email,
            'password': '1234567890',
            'password_confirm': '1234567890',
            'terms': True,
        })
        request.user = AnonymousUser()
        response = view(request)
        response.render()
        qs = User.objects.get(email=test_email)
        view = UserEndpoint.as_view({'get': 'activate'}, **UserEndpoint.activate.kwargs)
        token = UserValidateEmailRole.objects.get(user=qs).token
        url = '/api/users/activate/?token={}&email={}&subdomain=www'.format(token, test_email)
        request = self.factory.get(url, {})
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        request.user = AnonymousUser()
        response = view(request)
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)

    def testResetPassword(self):
        """
        Test creation of a user. No authentication
        """
        test_email = 'activate-user@test.com'
        view = UserEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'email': test_email,
            'password': '1234567890',
            'password_confirm': '1234567890',
            'terms': True,
        })
        request.user = AnonymousUser()
        response = view(request)
        response.render()
        qs = User.objects.get(email=test_email)
        view = UserEndpoint.as_view({'get': 'activate'}, **UserEndpoint.activate.kwargs)
        token = UserValidateEmailRole.objects.get(user=qs).token
        url = '/api/users/activate/?token={}&email={}&subdomain=www'.format(token, test_email)
        request = self.factory.get(url, {})
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        request.user = AnonymousUser()
        response = view(request)
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)

    def test_request_reset_password(self):
        from ..models import User
        alice = User.objects.create(
            email='alice@xyz.ct', username='alice', is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/request_reset_password/'
        data = {'email': alice.email}
        view = UserEndpoint.as_view(
            {'post': 'request_reset_password'},
            **UserEndpoint.request_reset_password.kwargs)
        request = self.factory.post(url, data)
        force_authenticate(request, user=alice)
        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)
