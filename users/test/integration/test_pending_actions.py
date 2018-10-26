from __future__ import absolute_import

from importlib import import_module

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser

from rest_framework import status

from acl.models import ActionControl
from blobs.test.util import APIUtilThumbnail, APIUtilDigitalWork
from ownership.models import OwnershipTransfer
from ownership.test.util import APIUtilTransfer
from piece.test.util import APIUtilPiece
from dynamicfixtures import mock_s3_bucket
from users.api import UserEndpoint
from users.models import UserValidateEmailRole, UserNeedsToRegisterRole, Role
from users.test.util import APIUtilUsers


# Test execute pending actions
class UsersEndpointPendingActionsTest(TestCase,
                                      APIUtilUsers,
                                      APIUtilThumbnail,
                                      APIUtilDigitalWork,
                                      APIUtilPiece,
                                      APIUtilTransfer):
    fixtures = ['licenses.json']

    def setUp(self):
        self.password = '0' * 10
        self.new_password = '1' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')
        self.user3_email = 'user3@test.com'

        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

    @mock_s3_bucket
    def test_execute_pending_actions(self):
        piece, editions = self.create_piece(self.user1, self.digitalwork_user1, self.thumbnail_user1, num_editions=2)
        edition = editions[0]

        # transfer to user3, who is not in the system
        self.create_transfer(self.user1, self.user3_email, edition.bitcoin_id, self.password)
        ownership_transfer = OwnershipTransfer.objects.get(edition=edition)

        # check user and roles
        try:
            user3 = User.objects.get(email=self.user3_email)
        except User.DoesNotExist:
            self.assertFalse(True, 'User was not created')

        user3_roles = Role.objects.filter(user=user3)
        self.assertEqual(len(user3_roles), 2)

        validate_role = UserValidateEmailRole.objects.get(user=user3)
        self.assertIsNone(validate_role.datetime_response)

        try:
            UserNeedsToRegisterRole.objects.get(user=user3, type="UserNeedsToRegisterRole")
        except UserNeedsToRegisterRole.DoesNotExist:
            self.assertFalse(True, 'UserNeedsToRegisterRole was not created')

        # check pending ownership
        self.assertEqual(ownership_transfer.edition.pending_new_owner, user3)
        self.assertEqual(ownership_transfer.edition.owner, self.user1)

        # check acls
        acl_user1 = ActionControl.objects.get(user=self.user1,
                                              piece=ownership_transfer.edition.parent,
                                              edition=ownership_transfer.edition)
        acl_user3 = ActionControl.objects.get(user=user3,
                                              piece=ownership_transfer.edition.parent,
                                              edition=ownership_transfer.edition)
        self.assertTrue(acl_user1.acl_withdraw_transfer)
        self.assertFalse(acl_user1.acl_unshare)
        self.assertTrue(acl_user3.acl_transfer)

        token = UserValidateEmailRole.objects.get(user=user3).token

        # signup & activate user3
        view = UserEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'email': self.user3_email,
            'password': '1234567890',
            'password_confirm': '1234567890',
            'terms': True,
            'token': token
        })
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore()
        request.user = AnonymousUser()

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)

        # check user roles
        validate_role = UserValidateEmailRole.objects.get(user=user3)
        self.assertIsNotNone(validate_role.datetime_response)
        with self.assertRaises(UserNeedsToRegisterRole.DoesNotExist):
            UserNeedsToRegisterRole.objects.get(user=user3, type="UserNeedsToRegisterRole")

        # check pending ownership
        ownership_transfer = OwnershipTransfer.objects.get(edition=edition)
        self.assertIsNone(ownership_transfer.edition.pending_new_owner)
        self.assertEqual(ownership_transfer.edition.owner, user3)

        # check acls
        acl_user1 = ActionControl.objects.get(user=self.user1,
                                              piece=ownership_transfer.edition.parent,
                                              edition=ownership_transfer.edition)
        acl_user3 = ActionControl.objects.get(user=user3,
                                              piece=ownership_transfer.edition.parent,
                                              edition=ownership_transfer.edition)
        self.assertFalse(acl_user1.acl_withdraw_transfer)
        self.assertTrue(acl_user1.acl_unshare)
        self.assertTrue(acl_user3.acl_transfer)
