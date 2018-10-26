from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.datetime_safe import datetime

import ast
from datetime import timedelta

import pytz
from util.util import randomStr


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    created_by = models.ForeignKey('oauth2_provider.Application', blank=True, null=True)
    hash_locally = models.BooleanField(default=False)
    language = models.CharField(default='en', max_length=10)
    copyright_association = models.CharField(max_length=100, blank=True, null=True)

class Role(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    datetime_response = models.DateTimeField(blank=True, null=True)

    # django auto-creates a reverse relation from User to RoleAtUserModel
    user = models.ForeignKey(User, related_name='role_at_user', null=True)

    role_str = models.TextField(blank=True, null=True)

    type = models.CharField(max_length=120, blank=True, null=True)

    @classmethod
    def create(cls, user, role):
        r = cls(user=user, role_str=str(role))
        r.type = cls.__name__
        return r

    @property
    def role(self):
        return ast.literal_eval(self.role_str) if self.role_str else None

    @role.setter
    def role(self, value):
        self.role_str = str(value)


class UserNeedsToRegisterRole(Role):

    class Meta:
        proxy = True


class UserTokenRole(Role):
    """
    Abstract class for generating tokens
    """

    class Meta:
        proxy = True

    @staticmethod
    def create(cls, user):
        r = cls(user=user, role_str=str(cls.generateToken()))
        r.type = cls.__name__
        return r

    @property
    def token(self):
        return self.role_str

    @property
    def isConfirmed(self):
        return not self.datetime_response is None

    def confirm(self):
        self.datetime_response = timezone.now()

    @staticmethod
    def generateToken():
        return randomStr(128)
        # return binascii.hexlify(os.urandom(128))


class UserValidateEmailRoleManager(models.Manager):
    """ Manager for UserValidateEmailRole """

    def get_queryset(self):
        return super(UserValidateEmailRoleManager, self).get_queryset() \
            .filter(type='UserValidateEmailRole')


class UserValidateEmailRole(UserTokenRole):
    """
    Has the user validated his email during sign up?
    """
    objects = UserValidateEmailRoleManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, user):
        return UserTokenRole.create(cls, user)

    @property
    def isExpired(self):
        return self.isConfirmed


class UserRequestResetPasswordRoleManager(models.Manager):
    """ Manager for UserRequestResetPasswordRole """

    def get_queryset(self):
        return super(UserRequestResetPasswordRoleManager, self).get_queryset() \
            .filter(type='UserRequestResetPasswordRole')


class UserRequestResetPasswordRole(UserTokenRole):
    """
    Create a token that expires when a user wants to reset his password
    """
    objects = UserRequestResetPasswordRoleManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, user):
        return UserTokenRole.create(cls, user)

    @property
    def isExpired(self):
        time_delta = timedelta(hours=settings.PASSWORD_RESET_EXPIRATION_TIME)
        return timezone.now() > self.datetime + time_delta or self.isConfirmed


class UserResetPasswordRoleManager(models.Manager):
    """ Manager for UserResetPasswordRole """

    def get_queryset(self):
        return super(UserResetPasswordRoleManager, self).get_queryset() \
            .filter(type='UserResetPasswordRole')


class UserResetPasswordRole(Role):
    """
    Remember that the user resetted his password, used upon SPOOL migrations
    """
    objects = UserResetPasswordRoleManager()

    class Meta:
        proxy = True

    @classmethod
    def create(cls, user):
        r = cls(user=user, role_str="")
        r.type = cls.__name__
        return r
