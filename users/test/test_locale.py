# -*- coding: utf-8 -*-

from django.conf import settings
from django.test import TestCase
from django.utils.translation import deactivate

from rest_framework import status
from rest_framework.test import APIClient


class UsersLocaleTest(TestCase):
    """
    Some tests to double-check that the translation mechanisms are working.

    """

    def tearDown(self):
        deactivate()

    def test_translation_for_login_with_non_existing_email(self):
        url = '/api/users/login/'
        data = {'email': 'alice@xyz.io', 'password': 'secret'}
        response = APIClient().post(url, data, HTTP_ACCEPT_LANGUAGE='fr')
        self.assertEqual(response.data['errors']['non_field_errors'][0],
                         'Courriel ou mot de passe incorrect')

    def test_translation_list_users_with_api_client(self):
        url = '/api/users/'
        response = APIClient().get(url, HTTP_ACCEPT_LANGUAGE='fr')
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, 'fr')
        self.assertEqual(response.data['detail'],
                         "Informations d'authentification non fournies.")

    def test_user_signup_email(self):
        # TODO use django test mail.outbox
        from users.test.util import APIUtilUsers

        APIUtilUsers.create_user('mysite_user',
                                 password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        url = '/api/users/'
        data = {
            'email': 'eve@xyz.io',
            'password': 'somesecret',
            'password_confirm': 'somesecret',
            'terms': True,
        }
        response = APIClient().post(url, data, HTTP_ACCEPT_LANGUAGE='fr')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
