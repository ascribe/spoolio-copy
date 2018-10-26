# -*- coding: utf-8 -*-

from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


from rest_framework import serializers

from core.fields import FormToSerializerBooleanField

from users.models import (
    UserProfile,
    UserNeedsToRegisterRole,
    UserValidateEmailRole,
    UserRequestResetPasswordRole
)

USER_PASSWORD_MAX_LENGTH = 60
WRONG_TOKEN_MESSAGE = _("The reset password token + link you choose is outdated. Update your emails and try again.")


class LoginForm(serializers.Serializer):
    email = serializers.EmailField(max_length=60, label='Email')
    password = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH)

    def validate(self, data):
        data['email'] = data['email'].lower()
        _verifyLogin(data['email'], data['password'])
        user = User.objects.get(email__iexact=data['email'])
        role = UserValidateEmailRole.objects.filter(user=user).order_by("-datetime")
        if len(role) and not role[0].isExpired:
            raise serializers.ValidationError({'email': _('Activate your account first by checking your email.')})

        return data


class ActivateForm(serializers.Serializer):
    email = serializers.EmailField(max_length=60, label='Email')
    token = serializers.CharField(max_length=1000)
    subdomain = serializers.CharField(max_length=20)

    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(_("Email %s not found.") % value)
        return user

    def validate(self, data):
        user = data['email']
        verify_token(user, data['token'])
        return data


class RequestResetPasswordForm(serializers.Serializer):
    email = serializers.EmailField(max_length=60, label='Email')

    def validate_email(self, value):
        try:
            return User.objects.get(email__iexact=value)
        except ObjectDoesNotExist:
            return None


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, max_length=USER_PASSWORD_MAX_LENGTH,
                                     min_length=10, label='Choose a password',
                                     error_messages={
                                         'blank': _('Password cannot be empty.'),
                                         'min_length': _('Password needs to contain at least 10 characters')
                                     })

    def validate_password(self, value):
        try:
            value.encode('ascii')
        except (UnicodeDecodeError, UnicodeEncodeError):
            raise serializers.ValidationError(_('Currently we do not support unicode characters in passwords.'))

        return value


class PasswordUpdateSerializer(PasswordSerializer):
    password_confirm = serializers.CharField(max_length=USER_PASSWORD_MAX_LENGTH,
                                             write_only=True,
                                             label='Confirm password')

    def validate_password_confirm(self, value):
        if value != self.initial_data.get('password'):
            raise serializers.ValidationError(_('Passwords do not match'))
        return value


class ResetPasswordForm(PasswordUpdateSerializer):
    email = serializers.EmailField(max_length=60, label='Email')
    token = serializers.CharField(max_length=1000)

    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Email %s not found." % value)
        return user

    def validate(self, data):
        user = data['email']
        # newest token first
        role = UserRequestResetPasswordRole.objects.filter(user=user).order_by("-datetime")
        if len(role) == 0:
            raise serializers.ValidationError(_("Couldn't find a request to reset your password"))
        role = role[0]
        if role.isExpired:
            raise serializers.ValidationError(
                _("Token expired, you can renew it by resetting your password once more")
            )
        if role.token != data['token']:
            raise serializers.ValidationError(WRONG_TOKEN_MESSAGE)
        return data


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=60, label='Email')

    def validate_email(self, value):
        value = value.lower()
        user = User.objects.filter(email=value)

        if len(user):
            # if there is a user, there may be a temporary profile (through invitation etc)
            if not userNeedsRegistration(value):
                raise serializers.ValidationError(_('An account with this email/username already exists.'))

        return value


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, max_length=30)

    def validate_username(self, value):
        if len(User.objects.filter(username=value)):
            raise serializers.ValidationError(_('Username not available'))
        return value


class BaseUserSerializer(EmailSerializer, UsernameSerializer):
    """
    Base serializer for the User Endpoint.

    Not meant to be used directly, only sublcassed
    """
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(max_length=60, label='Email')
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        try:
            user_profile = UserProfile.objects.get(user=obj)
        except ObjectDoesNotExist:
            user_profile = UserProfile.objects.create(user=obj)
            user_profile.save()
        return UserProfileSerializer(user_profile).data


class WebUserSerializer(BaseUserSerializer, PasswordUpdateSerializer):
    terms = FormToSerializerBooleanField(write_only=True,
                                         error_messages={'required': _('You must accept the terms and conditions.')},
                                         label='Terms')
    token = serializers.CharField(max_length=1000, required=False, write_only=True)

    def validate_terms(self, value):
        if not value:
            raise serializers.ValidationError('You must accept the terms and conditions.')
        return value

    def validate(self, data):
        if 'token' in data.keys():
            try:
                user = User.objects.get(email=data['email'])
                verify_token(user, data['token'])
            except User.DoesNotExist, serializers.ValidationError:
                del data['token']
        return data


class ApiUserSerializer(BaseUserSerializer, PasswordSerializer):
    pass


class UserProfileForm(serializers.ModelSerializer):

    email = serializers.EmailField(max_length=60, label='Email')
    # language = serializers.CharField(max_length=10)

    def validate_email(self, value):
        request = self.context.get('request')
        user = User.objects.get(email__iexact=value)
        if user != request.user:
            raise serializers.ValidationError('You are not allowed to set the profile of this user')
        return UserProfile.objects.get_or_create(user=user)[0]

    class Meta:
        model = UserProfile
        fields = ('hash_locally', 'email', 'copyright_association')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('hash_locally', 'language', 'copyright_association')


def userNeedsRegistration(email):
    from django.db.models import Q

    user = User.objects.filter(Q(email=email) | Q(username=email))
    if len(user) == 0:
        return None
    if len(UserNeedsToRegisterRole.objects.filter(user=user[0], type="UserNeedsToRegisterRole")):
        return user[0]


def _verifyLogin(email, password):
    """@brief -- will raise a ValidationError if user credentials are bad."""
    try:
        user = User.objects.get(email__iexact=email)
    except ObjectDoesNotExist:
        raise serializers.ValidationError(_('Email or password is incorrect'))
    # TODO Review. Authentication is done twice. Here & in UserEndpoint.login
    user = auth.authenticate(username=user.username, password=password)
    if user is None:
        raise serializers.ValidationError(_('Email or password is incorrect'))
    elif not user.is_active:
        raise serializers.ValidationError(_("Account with email '%s' is disabled.") % email)


def verify_password(username, password):
    # TODO Is it really necessary to authenticate the user here? If the goal is
    # to only check the password, .check_password() can be used, e.g.:
    # user = get_object_or_404(User, username=username)
    # user.check_password(password)
    # TODO Consider reviewing the reasons for this check.
    user = auth.authenticate(username=username, password=password)

    if user is None:
        raise serializers.ValidationError(_("Incorrect password"))
    return password


def verify_token(user, token):
    # newest token first
    role = UserValidateEmailRole.objects.filter(user=user).order_by("-datetime")
    if len(role) == 0:
        raise serializers.ValidationError(_("Couldn't find a request to activate your account"))
    role = role[0]
    if role.isExpired:
        raise serializers.ValidationError(_("Token expired, you can login using your password"))
    if role.token != token:
        raise serializers.ValidationError(WRONG_TOKEN_MESSAGE)


def createUsername(value):
    username = value
    increment = -1
    while True:
        if len(User.objects.filter(username=username)) == 0:
            break
        increment += 1
        username = value + "-" + str(increment)
    return username
