from __future__ import absolute_import, division, print_function

from importlib import import_module

from django.conf import settings
from django.test import TestCase

from rest_framework.test import APIRequestFactory
from rest_framework import status

from users.api import UserEndpoint


class LoginCsrfTest(TestCase):

    CSRF_FAILED_MSG = '<p>CSRF verification failed. Request aborted.</p>'
    MISSING_REFERER_MSG = (
        '<p>You are seeing this message because this HTTPS site requires a '
        '&#39;Referer header&#39; to be sent by your Web browser, but none '
        'was sent. This header is required for security reasons, to ensure '
        'that your browser is not being hijacked by third parties.</p>'
    )
    REASON_FOR_FAILURE_MSG = '<p>Reason given for failure:</p>'
    INVALID_REFERER_MSG = (
        '<pre>Referer checking failed - {bad_referer} does '
        'not match {good_referer}.</pre>'
    )

    def test_login_without_referer_nor_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **{'wsgi.url_scheme': 'https'})
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
        self.assertInHTML(self.MISSING_REFERER_MSG, response.content)

    def test_login_without_referer_and_with_invalid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_X_CSRFTOKEN': 'chocolatecookie',
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = 'vanillacookie'
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
        self.assertInHTML(self.MISSING_REFERER_MSG, response.content)

    def test_login_without_referer_and_with_valid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        csrf_token = 'cookiemonster'
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_X_CSRFTOKEN': csrf_token,
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = csrf_token
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
        self.assertInHTML(self.MISSING_REFERER_MSG, response.content)

    def test_login_with_invalid_referer_without_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        bad_referer = 'https://XYZ{}/'.format(host)
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': bad_referer,
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        with self.settings(DEBUG=True):
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
            self.assertInHTML(self.REASON_FOR_FAILURE_MSG, response.content)
            self.assertInHTML(
                self.INVALID_REFERER_MSG.format(
                    bad_referer=bad_referer, good_referer=good_referer),
                response.content)

    def test_login_with_invalid_referer_and_invalid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        bad_referer = 'https://XYZ{}/'.format(host)
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': bad_referer,
            'HTTP_X_CSRFTOKEN': 'chocolatecookie',
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = 'vanillacookie'
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        with self.settings(DEBUG=True):
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
            self.assertInHTML(self.REASON_FOR_FAILURE_MSG, response.content)
            self.assertInHTML(
                self.INVALID_REFERER_MSG.format(
                    bad_referer=bad_referer, good_referer=good_referer),
                response.content)

    def test_login_with_invalid_referer_and_valid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        bad_referer = 'https://XYZ{}/'.format(host)
        csrf_token = 'cookiemonster'
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': bad_referer,
            'HTTP_X_CSRFTOKEN': 'chocolatecookie',
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = csrf_token
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        with self.settings(DEBUG=True):
            response = view(request)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertInHTML(self.CSRF_FAILED_MSG, response.content)
            self.assertInHTML(self.REASON_FOR_FAILURE_MSG, response.content)
            self.assertInHTML(
                self.INVALID_REFERER_MSG.format(
                    bad_referer=bad_referer, good_referer=good_referer),
                response.content)

    def test_login_with_valid_referer_without_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': good_referer,
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {'success': True})

    def test_login_with_valid_referer_and_invalid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': good_referer,
            'HTTP_X_CSRFTOKEN': 'chocolatecookie',
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = 'vanillacookie'
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {'success': True})

    def test_login_with_valid_referer_and_valid_cookie(self):
        from ..models import User
        alice = User.objects.create(email='alice@xyz.ct',
                                    username='alice',
                                    is_active=True)
        alice.set_password('secret')
        alice.save()
        url = '/api/users/login/'
        data = {'email': alice.email, 'password': 'secret'}
        view = UserEndpoint.as_view({'post': 'login'},
                                    **UserEndpoint.login.kwargs)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        host = 'testserver:80'  # TODO if possible, set this programmatically
        good_referer = 'https://{}/'.format(host)
        csrf_token = 'cookiemonster'
        headers = {
            'wsgi.url_scheme': 'https',
            'HTTP_REFERER': good_referer,
            'HTTP_X_CSRFTOKEN': csrf_token,
        }
        # TODO when available, use secure parameter:
        # request = factory.post(url, data, secure=True)
        # as of 2015.08.03 it is on master:
        # https://github.com/tomchristie/django-rest-framework
        # in the meantime, we can use this nice trick from:
        # http://codeinthehole.com/writing/testing-https-handling-in-django/
        request = factory.post(url, data, **headers)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = csrf_token
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
