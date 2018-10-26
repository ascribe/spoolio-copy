from __future__ import absolute_import

from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from django.conf import settings
from rest_hooks.models import Hook
from users.test.util import APIUtilUsers
from webhooks.api import HookViewSet
from webhooks.test.util import APIUtilWebhook


# Test listing webhooks
# Test retrieving webhook
# Test webhook creation
# Test webhook deletion
class WebhookEndpointTest(TestCase, APIUtilUsers, APIUtilWebhook):

    def setUp(self):
        super(WebhookEndpointTest, self).setUp()

        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')

        self.webhooks_web = self.create_webhook(self.web_user, 'transfer.webhook', 'http://localhost.com/')

        self.factory = APIRequestFactory()

    def test_list_web(self):
        """
        Test that a web user can list his webhooks.
        He should not have access to the webhooks of others in the db.
        """
        view = HookViewSet.as_view({'get': 'list'})
        request = self.factory.get('/api/webhooks/')
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['webhooks'][0]['user'], self.web_user.id)

        force_authenticate(request, user=self.other_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 0)

    def test_retrieve_web(self):
        """
        Test that a user can only retrieve his own.
        """
        view = HookViewSet.as_view({'get': 'retrieve'})
        url = '/api/webhooks/{0}/'.format(self.webhooks_web.data['id'])
        request = self.factory.get(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.webhooks_web.data['id'])
        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.webhooks_web.data['id'])

        force_authenticate(request, user=self.other_user)

        response = view(request, pk=self.webhooks_web.data['id'])
        self.assertIs(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_web(self):
        """
        Test creation of a webhook
        """
        # not yet created during setup ('local' i.s.o. 'test')
        view = HookViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/webhooks/', {
            'event': 'share.webhook',
            'target': 'http://localhost.com'
        })
        force_authenticate(request, user=self.web_user)

        response = view(request)
        self.assertIs(response.status_code, status.HTTP_201_CREATED)
        db_hook = Hook.objects.get(id=response.data['id'])
        self.assertEqual(response.data['event'], db_hook.event)
        self.assertEqual(response.data['target'], db_hook.target)
        self.assertEqual(response.data['user'], db_hook.user_id)

    def test_delete_web(self):
        """
        Test deletion of a webhook
        """
        # not yet created during setup ('local' i.s.o. 'test')
        view = HookViewSet.as_view({'delete': 'destroy'})
        url = '/api/webhooks/{0}/'.format(self.webhooks_web.data['id'])
        request = self.factory.delete(url)

        force_authenticate(request, user=self.web_user)

        response = view(request, pk=self.webhooks_web.data['id'])
        self.assertIs(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(Hook.objects.filter(user=self.web_user)), 0)
