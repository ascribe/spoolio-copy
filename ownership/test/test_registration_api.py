import json

from django.core.urlresolvers import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from s3.test.mocks import MockAwsTestCase


class RegistrationTests(MockAwsTestCase):

    def test_retrieve_registration_with_integer_pk(self):
        from ..api import RegistrationEndpoint
        from ..models import OwnershipRegistration
        from dynamicfixtures import _registered_edition_alice
        edition = _registered_edition_alice()
        alice = edition.owner
        registration = OwnershipRegistration.objects.create(
            edition=edition,
            new_owner=alice,
            piece=edition.parent,
            type=OwnershipRegistration.__name__,
        )
        url = reverse('api:ownership:ownershipregistration-detail',
                      kwargs={'pk': registration.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = RegistrationEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=registration.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_registration_with_string_pk(self):
        from ..api import RegistrationEndpoint
        from ..models import OwnershipRegistration
        from dynamicfixtures import _registered_edition_alice
        edition = _registered_edition_alice()
        alice = edition.owner
        registration = OwnershipRegistration.objects.create(
            edition=edition,
            new_owner=alice,
            piece=edition.parent,
            type=OwnershipRegistration.__name__,
        )
        url = reverse('api:ownership:ownershipregistration-detail',
                      kwargs={'pk': registration.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = RegistrationEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=str(registration.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_non_existant_registration(self):
        """
        The goal of this test is to verify that a 404 (not found) is returned
        upon attempting to retrieve a registration that does not eixit.

        """
        from ..api import RegistrationEndpoint
        from ..models import OwnershipRegistration
        from dynamicfixtures import _alice
        alice = _alice()
        pk = 1
        self.assertFalse(OwnershipRegistration.objects.filter(pk=pk).exists())
        url = reverse('api:ownership:ownershipregistration-detail',
                      kwargs={'pk': pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = RegistrationEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_registration_with_alphanumerical_parameter(self):
        """
        The goal of this test is to verify that a 400 (bad request) is returned
        when passing an alphanumerical id instead of a numerical one.

        """
        from ..api import RegistrationEndpoint
        from ..models import OwnershipRegistration
        from dynamicfixtures import _registered_edition_alice
        edition = _registered_edition_alice()
        alice = edition.owner
        registration = OwnershipRegistration.objects.create(
            edition=edition,
            new_owner=alice,
            piece=edition.parent,
            type=OwnershipRegistration.__name__,
        )
        url = reverse('api:ownership:ownershipregistration-detail',
                      kwargs={'pk': registration.prev_btc_address})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = RegistrationEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=registration.prev_btc_address)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)
        self.assertEqual(response.data['reason'],
                         'id of object must be a number')

    def test_retrieve_registration_with_piece_field_only(self):
        """
        An `OwnershipRegistration` is always executed on a Piece level,
        which is why we need to make sure only to deliver the Piece as a
        `piece` property, and not also `edition`.
        """
        from ..api import RegistrationEndpoint
        from ..models import OwnershipRegistration
        from dynamicfixtures import _registered_edition_alice
        edition = _registered_edition_alice()
        alice = edition.owner
        registration = OwnershipRegistration.objects.create(
            edition=edition,
            new_owner=alice,
            piece=edition.parent,
            type=OwnershipRegistration.__name__,
        )
        url = reverse('api:ownership:ownershipregistration-detail',
                      kwargs={'pk': registration.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = RegistrationEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=registration.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('piece', response.data['registration'])
        self.assertIsNotNone('piece', response.data['registration'])
        self.assertNotIn('edition', response.data['registration'])
