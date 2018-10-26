# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import (
    force_authenticate, APITestCase, APIRequestFactory)


class S3BucketViewsTests(APITestCase):

    def test_success_redirect_endpoint(self):
        from s3.views import success_redirect_endpoint
        url = reverse('s3:s3_succes_endpoint')
        factory = APIRequestFactory()
        request = factory.get(url)
        response = success_redirect_endpoint(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_signature(self):
        from dynamicfixtures import _alice
        from s3.models import S3HttpRequest
        from util.util import hash_string
        alice = _alice()
        self.client.login(username=alice.username, password='secret-alice')
        url = reverse('s3:s3_sign')
        filename = 'dummy.jpg'
        key = 'local/{}/{}'.format(hash_string(str(alice.pk)), filename)
        data = {
            'conditions': [
                {'acl': 'public-read'},
                {'bucket': settings.AWS_STORAGE_BUCKET_NAME},
                {'Content-Type': 'image/jpeg'},
                {'success_action_status': '200'},
                {'key': key},
                {'x-amz-meta-qqfilename': filename},
                ['content-length-range', '0', settings.AWS_MAX_SIZE[0]],
            ],
        }
        self.assertFalse(S3HttpRequest.objects.exists())
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(S3HttpRequest.objects.exists())
        s3_http_request = S3HttpRequest.objects.get()
        self.assertEqual(
            s3_http_request.path,
            '/{}/{}'.format(settings.AWS_STORAGE_BUCKET_NAME, key),
        )

    def test_create_key_for_anonymous_user(self):
        from s3.views import create_key
        post_data = {
            'filename': 'dummy.jpg',
            'category': 'digitalwork',
            'uuid': '7aeaadeb-6ece-4a53-889d-114924ec5bb9',
        }
        url = reverse('s3:key')
        factory = APIRequestFactory()
        request = factory.post(url, post_data, format='json')
        response = create_key(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertDictEqual(
            response.data,
            {'detail': 'Authentication credentials were not provided.'},
        )

    def test_create_key_with_piece_id(self):
        from s3.views import create_key
        from dynamicfixtures import _alice, _piece_alice
        alice = _alice()
        piece = _piece_alice()
        post_data = {
            'filename': 'dummy.jpg',
            'category': 'thumbnail',
            'piece_id': piece.pk,
            'uuid': '7aeaadeb-6ece-4a53-889d-114924ec5bb9',
        }
        url = reverse('s3:key')
        factory = APIRequestFactory()
        request = factory.post(url, post_data, format='json')
        force_authenticate(request, user=alice)
        response = create_key(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('key', response.data)
        self.assertIn('/dummmy/thumbnail/', response.data['key'])

    def test_create_key_with_unicode_filename(self):
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('picosecret')
        alice.save()
        post_data = {
            'filename': '功夫.jpg',
            'category': 'digitalwork',
            'uuid': '7aeaadeb-6ece-4a53-889d-114924ec5bb9',
        }
        self.client.login(username='alice', password='picosecret')
        url = reverse('s3:key')
        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.data)
        self.assertEqual(response.content_type, 'application/json')

    def test_create_key_with_unicode_filename_without_uuid(self):
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('picosecret')
        alice.save()
        post_data = {
            'filename': '功夫.jpg',
            'category': 'dummy_category',
        }
        self.client.login(username='alice', password='picosecret')
        url = reverse('s3:key')
        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.data)
        self.assertEqual(response.content_type, 'application/json')

    def test_create_key_with_ascii_filename(self):
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('picosecret')
        alice.save()
        post_data = {
            'filename': 'blue.jpg',
            'category': 'digitalwork',
            'uuid': '7aeaadeb-6ece-4a53-889d-114924ec5bb9',
        }
        self.client.login(username='alice', password='picosecret')
        url = reverse('s3:key')
        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.data)
        self.assertEqual(response.content_type, 'application/json')

    def test_create_key_with_ascii_filename_without_uuid(self):
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('picosecret')
        alice.save()
        post_data = {
            'filename': 'blue.jpg',
            'category': 'dummy_category',
        }
        self.client.login(username='alice', password='picosecret')
        url = reverse('s3:key')
        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.data)
        self.assertEqual(response.content_type, 'application/json')

    def test_sign_url_with_authenticated(self):
        from s3.views import sign_url
        from dynamicfixtures import _alice, _piece_alice
        alice = _alice()
        piece = _piece_alice()
        url = reverse('s3:sign_url')
        url += '?key={}&title={}&artist_name={}'.format(piece.digital_work.key, piece.title, piece.artist_name)
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        response = sign_url(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sign_url_without_authentication(self):
        from s3.views import sign_url
        from dynamicfixtures import _piece_alice
        piece = _piece_alice()
        url = reverse('s3:sign_url')
        url += '?key={}&title={}&artist_name={}'.format(piece.digital_work.key, piece.title, piece.artist_name)
        factory = APIRequestFactory()
        request = factory.get(url)
        response = sign_url(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sign_url_with_unicode_and_without_authentication(self):
        from s3.views import sign_url
        from dynamicfixtures import _piece_alice
        piece = _piece_alice()
        url = reverse('s3:sign_url')
        url += '?key={}&title={}&artist_name={}'.format(piece.digital_work.key, '功夫', 'üöä')
        url = url.encode('ascii', 'ignore')
        factory = APIRequestFactory()
        request = factory.get(url)
        response = sign_url(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
