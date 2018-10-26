# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from django.conf import settings
from django.utils import timezone


pytestmark = pytest.mark.django_db


class TestRoleModel(object):

    def test_create_role(self, alice):
        from users.models import Role
        save_role = Role.create(alice, {'role': 'TESTROLE'})
        save_role.save()
        find_role = Role.objects.get(user=save_role.user)
        assert save_role.user.username == find_role.user.username
        assert save_role.type == find_role.type
        assert save_role.role == find_role.role
        assert save_role.type == 'Role'

    def test_update_role(self, alice):
        from users.models import Role
        save_role = Role.create(alice, {'role': 'TESTROLE'})
        save_role.save()
        save_role.role = {'role': 'UPDATE_ROLE'}
        save_role.save()
        find_role = Role.objects.get(user=save_role.user)
        assert save_role.user.username == find_role.user.username
        assert save_role.type == find_role.type
        assert find_role.role['role'] == 'UPDATE_ROLE'
        assert save_role.role == find_role.role


class TestUserNeedsToRegisterRoleModel(object):

    def test_create_role(self, alice):
        from users.models import UserNeedsToRegisterRole
        save_role = UserNeedsToRegisterRole.create(alice, {'role': 'TESTROLE'})
        save_role.save()
        find_role = UserNeedsToRegisterRole.objects.get(user=save_role.user)
        assert save_role.user.username == find_role.user.username
        assert save_role.type == find_role.type
        assert save_role.role == find_role.role
        assert save_role.type == 'UserNeedsToRegisterRole'

    def test_update_role(self, alice):
        from users.models import UserNeedsToRegisterRole
        save_role = UserNeedsToRegisterRole.create(alice, {'role': 'TESTROLE'})
        save_role.save()
        save_role.role = {'role': 'UPDATE_ROLE'}
        save_role.save()
        find_role = UserNeedsToRegisterRole.objects.get(user=save_role.user)
        assert save_role.user.username == find_role.user.username
        assert save_role.type == find_role.type
        assert find_role.role['role'] == 'UPDATE_ROLE'
        assert save_role.role == find_role.role


class TestUserRequestResetPasswordRoleModel(object):

    def test_is_expired_property(self):
        from ..models import UserRequestResetPasswordRole
        role = UserRequestResetPasswordRole.objects.create()
        assert not role.isExpired

    def test_is_expired_property_when_confirmed(self):
        from ..models import UserRequestResetPasswordRole
        role = UserRequestResetPasswordRole.objects.create(
            datetime_response=timezone.now(),
        )
        assert role.isExpired

    def test_is_expired_property_when_outdated(self, monkeypatch):
        from ..models import UserRequestResetPasswordRole
        role = UserRequestResetPasswordRole.objects.create()
        monkeypatch.setattr(settings, 'PASSWORD_RESET_EXPIRATION_TIME', 0)
        assert role.isExpired
