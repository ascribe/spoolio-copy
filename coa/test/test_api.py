from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import urlquote_plus

from rest_framework import status
from rest_framework.test import force_authenticate, APIRequestFactory

import responses
from boto.s3.key import Key

from dynamicfixtures import mock_s3_bucket


class CoaApiTests(TestCase):

    def test_list_non_authenticated(self):
        from ..api import CoaEndpoint
        url = reverse('api:coa:coafile-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        view = CoaEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertDictEqual(
            response.data,
            {'detail': 'Authentication credentials were not provided.'},
        )

    def test_list_with_no_coa(self):
        from ..api import CoaEndpoint
        from dynamicfixtures import _alice
        alice = _alice()
        url = reverse('api:coa:coafile-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('coas', response.data)
        self.assertListEqual(response.data['coas'], [])

    def test_list_with_one_coa_not_belonging_to_requesting_user(self):
        from ..api import CoaEndpoint
        from ..models import CoaFile
        from dynamicfixtures import _alice, _bob
        alice, bob = _alice(), _bob()
        CoaFile.objects.create(user=bob)
        url = reverse('api:coa:coafile-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('coas', response.data)
        self.assertListEqual(response.data['coas'], [])

    def test_list_with_one_coa_belonging_to_requesting_user(self):
        from ..api import CoaEndpoint
        from ..models import CoaFile
        from dynamicfixtures import _alice
        alice = _alice()
        coa_obj = CoaFile.objects.create(user=alice, coa_file='dummy.txt')
        url = reverse('api:coa:coafile-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('coas', response.data)
        self.assertEqual(len(response.data['coas']), 1)
        coa_data = response.data['coas'][0]
        self.assertIn('coa_file', coa_data)
        self.assertIn('url', coa_data)
        self.assertIn('url_safe', coa_data)
        self.assertEqual(coa_data['coa_file'], coa_obj.coa_file)
        self.assertEqual(coa_data['url'], coa_obj.url)
        self.assertEqual(coa_data['url_safe'], coa_obj.url_safe)

    def test_retrieve_coa_non_authenticated(self):
        from ..api import CoaEndpoint
        url = reverse('api:coa:coafile-detail', kwargs={'pk': 1})
        factory = APIRequestFactory()
        request = factory.get(url)
        view = CoaEndpoint.as_view({'get': 'retrieve'})
        response = view(request, {'pk': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertDictEqual(
            response.data,
            {'detail': 'Authentication credentials were not provided.'},
        )

    def test_retrieve_coa(self):
        from ..api import CoaEndpoint
        from dynamicfixtures import _alice
        from ..models import CoaFile
        alice = _alice()
        coa_obj = CoaFile.objects.create(user=alice, coa_file='dummy.txt')
        url = reverse('api:coa:coafile-detail', kwargs={'pk': coa_obj.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=coa_obj.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock_s3_bucket
    def test_verfiy_coa_with_authentication(self):
        from ..api import CoaEndpoint
        from ..models import generate_crypto_message
        from dynamicfixtures import _alice, _registered_edition_alice
        edition = _registered_edition_alice()
        alice = _alice()
        url = reverse('api:coa:coafile-verify-coa')
        message, _, signature = generate_crypto_message(edition)
        data = {
            'message': message,
            'signature': signature
        }
        request = APIRequestFactory().post(url, data, format='json')
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'post': 'verify_coa'},
                                   **CoaEndpoint.verify_coa.kwargs)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock_s3_bucket
    def test_verfiy_coa_without_authentication(self):
        from ..api import CoaEndpoint
        from ..models import generate_crypto_message
        from dynamicfixtures import _registered_edition_alice
        edition = _registered_edition_alice()
        url = reverse('api:coa:coafile-verify-coa')
        message, _, signature = generate_crypto_message(edition)
        data = {
            'message': message,
            'signature': signature
        }
        request = APIRequestFactory().post(url, data, format='json')
        view = CoaEndpoint.as_view({'post': 'verify_coa'},
                                   **CoaEndpoint.verify_coa.kwargs)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock_s3_bucket
    @responses.activate
    def test_create_coa(self):
        from ..api import CoaEndpoint
        from ..models import CoaFile
        from dynamicfixtures import _registered_edition_alice, _s3_bucket
        responses.add(
            responses.POST,
            settings.ASCRIBE_PDF_URL,
            json={},
            status=200,
            content_type='application/json',
        )
        edition = _registered_edition_alice()
        bucket = _s3_bucket()
        k = Key(bucket)
        k.key = edition.digital_work.key
        k.set_contents_from_string('white mountains')
        alice = edition.owner
        url = reverse('api:coa:coafile-list')
        factory = APIRequestFactory()
        data = {
            'bitcoin_id': edition.bitcoin_id,
        }
        request = factory.post(url, data, format='json')
        force_authenticate(request, user=alice)
        view = CoaEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('coa', response.data)
        self.assertIn('coa_file', response.data['coa'])
        self.assertIn('url', response.data['coa'])
        self.assertIn('url_safe', response.data['coa'])
        coa_key_prefix = edition.digital_work.key.replace(
            'digitalwork',
            'coa',
        ).rpartition('/')[0]
        stored_coa = (k for k in bucket.list(prefix=coa_key_prefix)).next()
        cloudfront_url = 'https://' + settings.AWS_CLOUDFRONT_DOMAIN
        coa_url = cloudfront_url + '/' + stored_coa.name
        coa_url_safe = cloudfront_url + '/' + urlquote_plus(stored_coa.name)
        self.assertEqual(response.data['coa']['coa_file'], stored_coa.name)
        self.assertEqual(response.data['coa']['url'], coa_url)
        self.assertEqual(response.data['coa']['url_safe'], coa_url_safe)
        coa_obj = CoaFile.objects.get()
        self.assertEqual(coa_obj.user, alice)
        self.assertEqual(coa_obj.edition, edition.pk)
        self.assertEqual(coa_obj.coa_file, stored_coa.name)
