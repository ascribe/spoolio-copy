# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from rest_framework.serializers import ValidationError

import pytest


User = get_user_model()

pytestmark = pytest.mark.django_db


class TestWebUserSerializer(object):

    def test_fields(self):
        from ..serializers import WebUserSerializer
        serializer = WebUserSerializer(data={})
        assert serializer.is_valid() is False
        assert serializer.errors == {
            'password': ['This field is required.'],
            'terms': ['You must accept the terms and conditions.'],
            'email': ['This field is required.'],
            'password_confirm': ['This field is required.']}

    def test_password_min_length(self):
        from ..serializers import WebUserSerializer
        serializer = WebUserSerializer(data={'password': '123'})
        assert serializer.is_valid() is False
        assert serializer.errors['password'] == [
            'Password needs to contain at least 10 characters']

    def test_password_unicode(self):
        from ..serializers import WebUserSerializer
        serializer = WebUserSerializer(data={'password': u'1234567890⅘⅘'})
        assert serializer.is_valid() is False
        assert serializer.errors['password'] == [
            'Currently we do not support unicode characters in passwords.']

    def test_password_confirm(self):
        from ..serializers import WebUserSerializer
        serializer = WebUserSerializer(data={'password': '1234567890',
                                             'email': 'test@test.com',
                                             'password_confirm': '12345678900',
                                             'terms': True})
        assert serializer.is_valid() is False
        assert serializer.errors == {
            'password_confirm': ['Passwords do not match']}

    def test_fields_complete(self):
        from ..serializers import WebUserSerializer
        serializer = WebUserSerializer(data={'password': '1234567890',
                                             'email': 'test@test.com',
                                             'password_confirm': '1234567890',
                                             'terms': True})
        assert serializer.is_valid() is True
        assert serializer.errors == {}

    def test_create_user_name(self, alice):
        from ..serializers import createUsername
        for i in range(10):
            username = createUsername(alice.username)
            email = '{}@test.com'.format(i)
            password = str(i)
            User.objects.create(
                username=username, email=email, password=password)
            assert username == '{}-{}'.format(alice.username, str(i))
            assert User.objects.get(
                username=username, email=email, password=password)


class TestLoginForm(object):

    def test_verify_login_with_non_existing_email(self):
        from ..serializers import _verifyLogin
        alice = User.objects.create(username='alice',
                                    email='alice@wonderland.xyz')
        alice.set_password('secret')
        with pytest.raises(ValidationError) as exc:
            _verifyLogin('bob@wonderland.xyz', 'secret')
        assert len(exc.value.detail) == 1
        assert exc.value.detail[0] == 'Email or password is incorrect'

    def test_verify_login_with_incorrect_password(self):
        from ..serializers import _verifyLogin
        alice = User.objects.create(username='alice',
                                    email='alice@wonderland.xyz')
        alice.set_password('secret')
        with pytest.raises(ValidationError) as exc:
            _verifyLogin(alice.email, 'wrong-password')
        assert len(exc.value.detail) == 1
        assert exc.value.detail[0] == 'Email or password is incorrect'


def test_verify_password(alice, alice_password):
    from ..serializers import verify_password
    password = verify_password(alice.username, alice_password)
    assert password == alice_password


def test_verify_apassword_for_non_existing_user():
    from ..serializers import verify_password
    with pytest.raises(ValidationError):
        verify_password('alice', 'alice-secret')


def test_verify_apassword_when_password_is_wrong(alice, alice_password):
    from ..serializers import verify_password
    with pytest.raises(ValidationError):
        verify_password(alice.username, alice_password + 'abc')
