from __future__ import absolute_import

from django.contrib.auth.models import User

from bitcoin.models import BitcoinWallet
from users.api import UserEndpoint
from users.models import UserRequestResetPasswordRole, UserResetPasswordRole, Role, UserProfile

__author__ = 'dimi'


class APIUtilUsers(object):
    @staticmethod
    def create_user(email, password='0000000000', application=None):
        # TODO create user differently -- no need to send an email for instance
        return UserEndpoint._createNewUser(email, password,
                                           application=application)

    @staticmethod
    def create_user_needs_to_register(email):
        return UserEndpoint._createNewUser(email, '0' * 10, invited=True)

    @staticmethod
    def request_reset_password(user):
        role = UserRequestResetPasswordRole.create(user)
        role.save()
        return role.token

    @staticmethod
    def reset_password(user, password):
        UserResetPasswordRole.create(user=user).save()
        user.set_password(password)
        user.save()
        request_role = UserRequestResetPasswordRole.objects.filter(user=user).order_by("-datetime")[0]
        request_role.confirm()
        request_role.save()
        # update bitcoin wallet
        wallet = BitcoinWallet.objects.get(user=user)
        pubkey = BitcoinWallet.pubkeyFromPassword(user, password)
        wallet.public_key = pubkey
        wallet.save()

    @staticmethod
    def update_user_id(user, new_id):
        old_id = user.id
        User.objects.filter(id=old_id).update(id=new_id)
        UserProfile.objects.filter(user_id=old_id).update(user_id=new_id)
        BitcoinWallet.objects.filter(user_id=old_id).update(user_id=new_id)
        Role.objects.filter(user_id=old_id).update(user_id=new_id)
