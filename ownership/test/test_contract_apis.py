# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
from datetime import datetime, timedelta

import pytz

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate


class ContractEndpointTests(TestCase):
    def _create_blob(self):
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'
        return OtherData.objects.create(other_data_file=FIX_KEY_PNG)

    def test_list_contracts_non_authenticated(self):
        from ..api import ContractEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_contract_non_authenticated(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract.pk})
        request = factory.get(url)
        view = ContractEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=contract.pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_contract_non_authenticated(self):
        from ..api import ContractEndpoint
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create()
        data = {'issuer': issuer.pk, 'blob': blob.pk}
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.post(url, data=data, format='json')
        view = ContractEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @unittest.skip('not implemented yet')
    def test_update_contract_non_authenticated(self):
        raise NotImplementedError

    def test_destroy_contract_non_authenticated(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create()
        contract_pk = Contract.objects.create(issuer=issuer, blob=blob).pk
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract_pk})
        request = factory.delete(url)
        view = ContractEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=contract_pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_contracts(self):
        from ..api import ContractEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url)
        joe = User.objects.create(username='joe', email='joe@qtm.cpu')
        force_authenticate(request, user=joe)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_contracts_for_issuer(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer_one = User.objects.create(username='issuer_one',
                                         email='issuer_one@xyz.ct')
        issuer_two = User.objects.create(username='issuer_two',
                                         email='issuer_two@xyz.ct')
        blob = self._create_blob()
        contract_one = Contract.objects.create(issuer=issuer_one, blob=blob)
        Contract.objects.create(issuer=issuer_two, blob=blob)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url)
        force_authenticate(request, user=issuer_one)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], contract_one.pk)

    def test_list_active_contracts(self):
        """
        Tests that filering for contracts that are active works. The filter is
        done via a query parameter: "is_active".

        """
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        active_contract = Contract.objects.create(issuer=issuer,
                                                  blob=blob,
                                                  is_active=True)
        Contract.objects.create(issuer=issuer, blob=blob, is_active=False)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url, {'is_active': True})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], active_contract.pk)

    def test_list_inactive_contracts(self):
        """
        Tests that filering for contracts that are inactive works. The filter
        is done via a query parameter: "is_active".

        """
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        inactive_contract = Contract.objects.create(issuer=issuer,
                                                    blob=blob,
                                                    is_active=False)
        Contract.objects.create(issuer=issuer, blob=blob, is_active=True)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url, {'is_active': False})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         inactive_contract.pk)

    def test_list_public_contracts(self):
        """
        Tests that filering for contracts that are public works. The filter is
        done via a query parameter: "is_public".

        """
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        blob.user = issuer
        blob.save()
        public_contract = Contract.objects.create(
            issuer=issuer, blob=blob, name='public', is_public=True)
        Contract.objects.create(
            issuer=issuer, blob=blob, name='private', is_public=False)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url, {'is_public': True})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], public_contract.pk)

    def test_list_public_contracts_case_insensitive(self):
        """
        Tests that filering for contracts that are public works and is case
        insensitive. The filter is done via a query parameter: "is_public".

        """
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        blob.user = issuer
        blob.save()
        public_contract = Contract.objects.create(
            issuer=issuer, blob=blob, name='public', is_public=True)
        Contract.objects.create(
            issuer=issuer, blob=blob, name='private', is_public=False)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url, {'is_public': 'true'})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], public_contract.pk)

    def test_list_private_contracts(self):
        """
        Tests that filering for contracts that are privatec works. The filter is
        done via a query parameter: "is_public".

        """
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        blob.user = issuer
        blob.save()
        private_contract = Contract.objects.create(
            issuer=issuer, blob=blob, name='public', is_public=False)
        Contract.objects.create(
            issuer=issuer, blob=blob, name='private', is_public=True)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.get(url, {'is_public': False})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         private_contract.pk)

    def test_retrieve_contract_for_issuer(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from ..serializers import ContractSerializer
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = self._create_blob()
        contract = Contract.objects.create(issuer=issuer, blob=blob, is_public=True)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract.pk})
        request = factory.get(url, {'issuer': issuer.email})
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=contract.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data,
                             ContractSerializer(contract).data)

    @unittest.skip('changed to blob not required - need to double check')
    def test_create_contract_without_blob(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        data = {'issuer': issuer.pk}
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.post(url, data=data, format='json')
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data,
                             {'blob': ['This field is required.']})
        self.assertFalse(Contract.objects.exists())

    def test_create_contract_with_blob(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from ..serializers import ContractForm
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create(user=issuer,
                                        other_data_file=FIX_KEY_PNG)
        data = {
            'issuer': issuer.pk,
            'blob': blob.other_data_file,
            'name': 'green',
        }
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.post(url, data=data, format='json')
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contract = Contract.objects.get(id=response.data['contract']['id'])
        self.assertEqual(contract.blob, blob)
        self.assertDictEqual(ContractForm(contract).data, response.data['contract'])

    @unittest.skip('need to move under contract agreement tests')
    def test_create_contract_with_appendix(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from ..serializers import ContractSerializer
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create(user=issuer)
        appendix = {'terms and conditions': 'xyz'}
        data = {
            'issuer': issuer.pk,
            'blob': blob.pk,
            'appendix': appendix,
        }
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-list')
        request = factory.post(url, data=data, format='json')
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contract = Contract.objects.get(id=response.data['id'])
        self.assertDictEqual(contract.appendix, appendix)
        self.assertDictEqual(ContractSerializer(contract).data,
                             response.data)

    def test_update_contract(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob_0 = OtherData.objects.create(user=issuer, key='key_0')
        contract = Contract.objects.create(
            issuer=issuer,
            blob=blob_0,
            name='awesome_deal'
        )
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract.pk})
        blob_1 = OtherData.objects.create(user=issuer, key='key_1')
        data = {
            'name': contract.name,
            'blob': blob_1.key,
        }
        request = factory.put(url, data=data)
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'put': 'update'})
        response = view(request, pk=contract.pk)
        contract = Contract.objects.get(pk=contract.pk)
        latest_contract = Contract.objects.get(name=contract.name,
                                               is_active=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(contract.is_active)
        self.assertEqual(response.data['contract']['id'], latest_contract.pk)
        self.assertEqual(latest_contract.blob, blob_1)
        self.assertNotEqual(latest_contract.pk, contract.pk)

    def test_destroy_contract(self):
        from ..api import ContractEndpoint
        from ..models import Contract
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create()
        contract_pk = Contract.objects.create(issuer=issuer, blob=blob).pk
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract_pk})
        request = factory.delete(url)
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=contract_pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Contract.objects.get(pk=contract_pk).datetime_deleted)

    def test_destroy_contract_with_existing_contractagreement(self):
        from ..api import ContractEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        issuer = User.objects.create(username='issuer', email='issuer@xyz.ct')
        blob = OtherData.objects.create()
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        ca = ContractAgreement.objects.create(contract=contract, signee=alice)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contract-detail',
                      kwargs={'pk': contract.pk})
        request = factory.delete(url)
        force_authenticate(request, user=issuer)
        view = ContractEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=contract.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Contract.objects.get(pk=contract.pk).datetime_deleted)
        self.assertIsNotNone(ContractAgreement.objects.get(pk=ca.pk).datetime_deleted)

    @unittest.skip('not implemented yet')
    def test_contracts_issuer_endpoint(self):
        raise NotImplementedError

    @unittest.skip('not fully implemented yet')
    def test_contracts_signee_endpoint(self):
        from ..api import ContractEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        gluonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        photonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        ContractAgreement.objects.create(contract=gluonic_contract, signee=alice)
        ContractAgreement.objects.create(contract=photonic_contract, signee=alice)
        # contract history for bob
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        ContractAgreement.objects.create(contract=photonic_contract, signee=bob)
        url = reverse('api:ownership:contract-signee', kwargs={'pk': alice.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=merlin)
        view = ContractEndpoint.as_view({'get': 'signee'})
        response = view(request, pk=alice.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_pending_contracts_for_signee(self):
        """
        Filter for contracts that belong to the given signee, and have
        no datetime_accepted nor datettime_rejected set.

        actors:
            merlin - issuer of contracts
            alice - signee
            bob - signee
        objects:
            contract for alice with three diffrent contract agreements
                (pending, accepted, rejected)
            contract for bob with same histories

        """
        from ..api import ContractEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        gluonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        photonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        # bosonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        datetime_sent = datetime.utcnow().replace(tzinfo=pytz.UTC)
        datetime_accepted = datetime_sent - timedelta(days=1)
        datetime_rejected = datetime_sent - timedelta(days=3)
        ContractAgreement.objects.create(
            contract=gluonic_contract,
            signee=alice,
        )
        ContractAgreement.objects.create(
            contract=gluonic_contract,
            signee=alice,
            datetime_accepted=datetime_accepted
        )
        ContractAgreement.objects.create(
            contract=gluonic_contract,
            signee=alice,
            datetime_accepted=datetime_rejected
        )
        # ContractAgreement.objects.create(contract=photonic_contract, signee=alice)
        # contract history for bob
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        ContractAgreement.objects.create(contract=photonic_contract, signee=bob)

        url = reverse('api:ownership:contract-pending', kwargs={'pk': alice.pk})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=merlin)
        view = ContractEndpoint.as_view({'get': 'pending'})
        response = view(request, pk=alice.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unittest.skip('not implemented yet')
    def test_list_pending_contracts_for_issuer(self):
        """
        Filter for contracts that belong to the given issuer,
        and have no datetime_accepted nor datettime_rejected set.

        """
        raise NotImplementedError

    @unittest.skip('not implemented yet')
    def test_options_non_authenticated(self):
        raise NotImplementedError

    def test_post_options(self):
        """
        The goal of this test is to check that the returned meta data is as we
        expect.

        """
        from ..api import ContractEndpoint
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        User.objects.create(username='alice', email='alice@xyz.ct')
        url = reverse('api:ownership:contract-list')
        factory = APIRequestFactory()
        request = factory.options(url)
        force_authenticate(request, user=merlin)
        view = ContractEndpoint.as_view({'post': 'options'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('choices', response.data['actions']['POST']['issuer'])
        self.assertNotIn('choices', response.data['actions']['POST']['blob'])

    @unittest.skip('not fully implemented yet')
    def test_put_options(self):
        """
        The goal of this test is to check that the returned meta data is as we
        expect.

        """
        raise NotImplementedError

    @unittest.skip('not implemented yet')
    def test_head_non_authenticated(self):
        raise NotImplementedError

    @unittest.skip('not implemented yet')
    def test_head(self):
        raise NotImplementedError


class ContractAgreementEndpointNonAuthenticatedTests(TestCase):
    def test_list_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.post(url, data={}, format='json')
        view = ContractAgreementEndpoint.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail', kwargs={'pk': 1})
        request = factory.post(url)
        view = ContractAgreementEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail', kwargs={'pk': 1})
        request = factory.post(url)
        view = ContractAgreementEndpoint.as_view({'put': 'update'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail', kwargs={'pk': 1})
        request = factory.post(url)
        view = ContractAgreementEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @unittest.skip('not yet implemented')
    def test_pending_non_authenticated(self):
        raise NotImplementedError

    def test_accept_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail', kwargs={'pk': 1})
        request = factory.patch(url)
        view = ContractAgreementEndpoint.as_view({'patch': 'accept'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reject_non_authenticated(self):
        from ..api import ContractAgreementEndpoint
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail', kwargs={'pk': 1})
        request = factory.patch(url)
        view = ContractAgreementEndpoint.as_view({'patch': 'reject'})
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @unittest.skip('not yet implemented')
    def test_options_non_authenticated(self):
        raise NotImplementedError

    @unittest.skip('not yet implemented')
    def test_head_non_authenticated(self):
        raise NotImplementedError


class ContractAgreementEndpointTests(TestCase):
    """
    Tests for the ``ContractAgreementEndpoint`` view, when the requesting user
    is a signee. The ``ContractAgreementEndpoint`` provides operations to act on
    ``ContractAgreement`` objects. The supported operations for signees are:

        * list ``ContractAgreement`` objects (GET)
        * create a ``ContractAgreement`` objects (POST)
        * retrieve a ``ContractAgreement`` object (GET)
        * update a ``ContractAgreement`` object (PUT/PATCH)
        * destroy a ``ContractAgreement`` object (DELETE)

    A signee is allowed to create a ``ContractAgreement`` objects only if the
    given contract is "public", i.e.: ``contract.is_public == True``.

    Additionally, the following custom routes need to be tested:
        * ``/pending`` - list contract agreements that are in a pending state
        * ``/accept`` - accept a contract agreement
        * ``/reject`` - reject a contract agreement

    """

    def test_list_contract_agreements_for_signee(self):
        """
        Tests that a requesting user (alice) only sees the contract agreement
        instances she has access to.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        ContractAgreement.objects.create(contract=contract, signee=alice)
        # contract history for bob
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        ContractAgreement.objects.create(contract=contract, signee=bob)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         ContractAgreement.objects.get(signee=alice).pk)

    def test_list_contract_agreements_for_given_issuer(self):
        """
        Use case:
            A requesting user (signee) wishes to list contract agreements for
            a given issuer.

            We assume that a signee can have contract agreements with various
            issuers, and at some point in time wishes to view the contract
            agreements for a specific issuer.

        Test data:
            - One signee: alice
            - Two issuers: merlin & yoda
            - One contract agreement between alice & merlin.
            - One contract agreement between alice & yoda.

        Request:
            Fetch list of contract agreements for alice, issued by merlin.
        Response:
            Only one contract agreement between alice & merlin.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        alice = User.objects.create(username='alice', email='alice@abc.pq')
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        yoda = User.objects.create(username='yoda', email='yoda@stars.io')
        merlin_blob = OtherData.objects.create(user=merlin,
                                               other_data_file=FIX_KEY_PNG)
        yoda_blob = OtherData.objects.create(user=yoda,
                                             other_data_file=FIX_KEY_PNG)
        merlin_contract = Contract.objects.create(issuer=merlin,
                                                  blob=merlin_blob,
                                                  name='magic')
        yoda_contract = Contract.objects.create(issuer=yoda,
                                                blob=yoda_blob,
                                                name='force')
        ca_merlin = ContractAgreement.objects.create(signee=alice,
                                                     contract=merlin_contract)
        ContractAgreement.objects.create(signee=alice, contract=yoda_contract)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url, {'issuer': merlin.email})
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], ca_merlin.pk)

    def test_list_pending_contract_agreements(self):
        """
        Use case:
            A requesting user (signee) wishes to list pending contract
            agreements.

        Test data:
            - One signee: alice
            - One issuer: merlin
            - One contract: issued by merlin
            - One pending contract agreement
            - One accepted contract agreement
            - One rejected contract agreement

        Request:
            Fetch list of pending contract agreements for alice, using query
            parameter: "pending".
        Response:
            List of pending contract agreements.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        alice = User.objects.create(username='alice', email='alice@abc.pq')
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create(user=merlin,
                                        other_data_file=FIX_KEY_PNG)
        contract = Contract.objects.create(
            issuer=merlin, blob=blob, name='magic')
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        pending_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract
        )
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url, {'pending': True})
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         pending_contract_agreement.pk)

    def test_list_accepted_contract_agreements(self):
        """
        Use case:
            A requesting user (signee) wishes to list accepted contract
            agreements.

        Test data:
            - One signee: alice
            - One issuer: merlin
            - One contract: issued by merlin
            - One pending contract agreement
            - One accepted contract agreement
            - One rejected contract agreement

        Request:
            Fetch list of accepted contract agreements for alice, using query
            parameter: "accepted".
        Response:
            The accepted contract agreement, in a list.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        alice = User.objects.create(username='alice', email='alice@abc.pq')
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create(user=merlin,
                                        other_data_file=FIX_KEY_PNG)
        contract = Contract.objects.create(
            issuer=merlin, blob=blob, name='magic')
        ContractAgreement.objects.create(signee=alice, contract=contract)
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        accepted_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url, {'accepted': True})
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         accepted_contract_agreement.pk)

    def test_list_pending_contract_agreements_for_given_issuer(self):
        """
        Use case:
            A requesting user (signee) wishes to list pending contract
            agreements for a given issuer.

            We assume that a signee can have contract agreements with various
            issuers, and at some point in time wishes to view the contract
            agreements for a specific issuer. Furthermore, the request requires
            contract agreements which are in a pending state.

        Test data:
            - One signee: alice
            - Two issuers: merlin & yoda
            - One pending contract agreement between alice & merlin.
            - One accepted contract agreement between alice & merlin.
            - One rejected contract agreement between alice & merlin.
            - One pending contract agreement between alice & yoda.
            - One accepted contract agreement between alice & yoda.
            - One rejected contract agreement between alice & yoda.

        Request:
            Fetch list of pending contract agreements for alice, issued by
            merlin.
        Response:
           The pending contract agreement between alice & merlin.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        alice = User.objects.create(username='alice', email='alice@abc.pq')
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        yoda = User.objects.create(username='yoda', email='yoda@stars.io')
        merlin_blob = OtherData.objects.create(user=merlin,
                                               other_data_file=FIX_KEY_PNG)
        yoda_blob = OtherData.objects.create(user=yoda,
                                             other_data_file=FIX_KEY_PNG)
        merlin_contract = Contract.objects.create(issuer=merlin,
                                                  blob=merlin_blob,
                                                  name='magic')
        yoda_contract = Contract.objects.create(issuer=yoda,
                                                blob=yoda_blob,
                                                name='force')
        ContractAgreement.objects.create(
            signee=alice,
            contract=merlin_contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=merlin_contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        pending_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=merlin_contract
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=yoda_contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=yoda_contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=yoda_contract
        )
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-list')
        request = factory.get(url, {'issuer': merlin.email, 'pending': True})
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'],
                         pending_contract_agreement.pk)

    def test_retrieve_contract_agreement_for_non_authorized_signee(self):
        """
        Tests that a requesting user (bob) cannot retrieve a ContractAgreement
        instance that deos not belong to him.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        contract_history_of_alice = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail',
                      kwargs={'pk': contract_history_of_alice.pk})
        request = factory.get(url)
        force_authenticate(request, user=bob)
        view = ContractAgreementEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=contract_history_of_alice.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_for_authorized_signee(self):
        """
        Tests that a requesting user (alice) can retrieve a ContractAgreement
        instance that belongs to her.

        """
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        contract_history_of_alice = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail',
                      kwargs={'pk': contract_history_of_alice.pk})
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'retrieve'})
        response = view(request, pk=contract_history_of_alice.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], contract_history_of_alice.pk)

    def test_route_list_pending_contract_agreements(self):
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        # contract
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        gluonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        photonic_contract = Contract.objects.create(issuer=merlin, blob=blob)
        # contract history for alice
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        datetime_sent = datetime.utcnow().replace(tzinfo=pytz.UTC)
        datetime_accepted = datetime_sent - timedelta(days=1)
        datetime_rejected = datetime_sent - timedelta(days=3)
        ContractAgreement.objects.create(
            signee=alice,
            contract=gluonic_contract
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=gluonic_contract,
        )
        pending_contract_agreement_3 = ContractAgreement.objects.create(
            signee=alice,
            contract=photonic_contract,
        )
        # contract history for bob
        bob = User.objects.create(username='bob', email='bob@xyz.ct')
        ContractAgreement.objects.create(signee=bob,
                                         contract=photonic_contract)
        url = reverse('api:ownership:contractagreement-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'get': 'pending'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # there should be only one pending, as the previous ones get deleted
        self.assertEqual(response.data['count'], 1)
        result_ids = [obj['id'] for obj in response.data['results']]
        self.assertIn(pending_contract_agreement_3.pk, result_ids)
        ContractAgreement.objects.create(
            signee=alice,
            contract=gluonic_contract,
            datetime_accepted=datetime_accepted
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=gluonic_contract,
            datetime_rejected=datetime_rejected
        )
        # there should be none pending, as the previous ones get deleted and the latest is rejected
        view = ContractAgreementEndpoint.as_view({'get': 'pending'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_accept_contract_agreement(self):
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=merlin, blob=blob)
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        self.assertIsNone(contract_agreement.datetime_accepted)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail',
                      kwargs={'pk': contract_agreement.pk})
        request = factory.patch(url)
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'patch': 'accept'})
        response = view(request, pk=contract_agreement.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contract_agreement = ContractAgreement.objects.get()
        self.assertIsNotNone(contract_agreement.datetime_accepted)

    def test_reject_contract_agreement(self):
        from ..api import ContractAgreementEndpoint
        from ..models import Contract, ContractAgreement
        from blobs.models import OtherData
        merlin = User.objects.create(username='merlin', email='merlin@xyz.ct')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=merlin, blob=blob)
        alice = User.objects.create(username='alice', email='alice@xyz.ct')
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        self.assertIsNone(contract_agreement.datetime_rejected)
        factory = APIRequestFactory()
        url = reverse('api:ownership:contractagreement-detail',
                      kwargs={'pk': contract_agreement.pk})
        request = factory.patch(url)
        force_authenticate(request, user=alice)
        view = ContractAgreementEndpoint.as_view({'patch': 'reject'})
        response = view(request, pk=contract_agreement.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contract_agreement = ContractAgreement.objects.get()
        self.assertIsNotNone(contract_agreement.datetime_rejected)
