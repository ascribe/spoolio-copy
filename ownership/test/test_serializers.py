# coding=utf-8

import unittest
from collections import namedtuple
from email.utils import parseaddr

import pytest

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from rest_framework import serializers


@pytest.mark.django_db
class TestOwnershipSerializer(object):

    def test_deserialization_without_exposing_user_profiles(self, ownership):
        from ..serializers import OwnershipEditionSerializer
        serializer = OwnershipEditionSerializer(ownership)
        assert 'id' in serializer.data
        assert 'prev_owner' in serializer.data
        assert 'new_owner' in serializer.data
        # We need to make sure, not to expose private information of the user
        assert 'profile' not in serializer.data['prev_owner']
        assert 'profile' not in serializer.data['new_owner']
        # but only the email address of the user
        assert parseaddr(
            serializer.data['prev_owner'])[1] == serializer.data['prev_owner']
        assert parseaddr(
            serializer.data['new_owner'])[1] == serializer.data['new_owner']

    def test_deserialization_with_action_on_edition(self, ownership):
        from ..serializers import OwnershipEditionSerializer
        serializer = OwnershipEditionSerializer(ownership)
        assert 'piece' not in serializer.data
        assert 'edition' in serializer.data
        assert ownership.edition.pk == serializer.data['edition']['id']

    def test_deserialization_with_action_on_piece(self, ownership):
        from ..serializers import OwnershipPieceSerializer
        serializer = OwnershipPieceSerializer(ownership)
        assert 'edition' not in serializer.data
        assert 'piece' in serializer.data
        assert ownership.piece.pk == serializer.data['piece']['id']

    def test_time_bound_edition_loan_deserialization(self, loan_edition):
        from ..serializers import LoanSerializer
        serializer = LoanSerializer(loan_edition)
        assert 'startdate' in serializer.data
        assert 'enddate' in serializer.data
        assert (serializer.data['startdate'] ==
                loan_edition.datetime_from.strftime('%Y-%m-%d'))
        assert (serializer.data['enddate'] ==
                loan_edition.datetime_to.strftime('%Y-%m-%d'))

    def test_time_bound_piece_loan_deserialization(self, loan_piece):
        from ..serializers import LoanPieceSerializer
        serializer = LoanPieceSerializer(loan_piece)
        assert 'startdate' in serializer.data
        assert 'enddate' in serializer.data
        assert (serializer.data['startdate'] ==
                loan_piece.datetime_from.strftime('%Y-%m-%d'))
        assert (serializer.data['enddate'] ==
                loan_piece.datetime_to.strftime('%Y-%m-%d'))

    def test_time_unbound_ownership_deserialization(self, ownership):
        from ..serializers import OwnershipEditionSerializer
        serializer = OwnershipEditionSerializer(ownership)
        assert 'startdate' not in serializer.data
        assert 'enddate' not in serializer.data


class TestTransferModalFormSerializer(object):

    def test_fields(self):
        from ownership.serializers import TransferModalForm
        serializer = TransferModalForm(data={})
        assert serializer.is_valid() is False
        assert serializer.errors['password'] == ['This field is required.']
        assert serializer.errors['transferee'] == [u'This field is required.']
        assert serializer.errors['bitcoin_id'] == [u'This field is required.']


@pytest.mark.django_db
def test_transfer_to_self(registered_edition_alice, alice, alice_password):
    from ownership.serializers import TransferModalForm
    data = {
        'transferee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = TransferModalForm(data=data, context=context)
    assert not serializer.is_valid()
    assert 'transferee' in serializer.errors


@pytest.mark.django_db
def test_transfer_to_owner(registered_edition_alice, alice, alice_password):
    from ownership.serializers import TransferModalForm
    data = {
        'transferee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = TransferModalForm(data=data, context=context)
    with pytest.raises(serializers.ValidationError):
        serializer._validate_acl(registered_edition_alice, alice.email)


@pytest.mark.django_db
def test_consign_to_self(registered_edition_alice, alice, alice_password):
    from ownership.serializers import ConsignModalForm
    data = {
        'consignee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = ConsignModalForm(data=data, context=context)
    assert not serializer.is_valid()
    assert 'consignee' in serializer.errors


@pytest.mark.django_db
def test_consign_to_owner(registered_edition_alice, alice, alice_password):
    from ownership.serializers import ConsignModalForm
    data = {
        'consignee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = ConsignModalForm(data=data, context=context)
    with pytest.raises(serializers.ValidationError):
        serializer._validate_acl(registered_edition_alice, alice.email)


@pytest.mark.django_db
def test_loan_to_self(registered_edition_alice, alice, alice_password):
    from ownership.serializers import LoanModalForm
    data = {
        'loanee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = LoanModalForm(data=data, context=context)
    assert not serializer.is_valid()
    assert 'loanee' in serializer.errors


@pytest.mark.django_db
def test_loan_to_owner(registered_edition_alice, alice, alice_password):
    from ownership.serializers import LoanModalForm
    data = {
        'loanee': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = LoanModalForm(data=data, context=context)
    with pytest.raises(serializers.ValidationError):
        serializer._validate_acl(registered_edition_alice, alice.email)


@pytest.mark.django_db
def test_share_to_self(registered_edition_alice, alice, alice_password):
    from ownership.serializers import ShareModalForm
    data = {
        'share_emails': alice.email,
        'bitcoin_id': registered_edition_alice.bitcoin_id,
        'password': alice_password,
    }

    context = {
        'request': namedtuple('Request', 'user')(alice)
    }

    serializer = ShareModalForm(data=data, context=context)
    assert not serializer.is_valid()
    assert serializer.errors['share_emails']


class ContractModelSerializerTests(TestCase):
    def test_basic_deserialization(self):
        from ..models import Contract
        from ..serializers import ContractSerializer
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create(user=issuer, key=FIX_KEY_PNG)
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        serializer = ContractSerializer(contract)
        self.assertIn('id', serializer.data)
        self.assertIn('issuer', serializer.data)
        self.assertIn('blob', serializer.data)
        self.assertIn('datetime_created', serializer.data)
        self.assertEqual(serializer.data['id'], contract.pk)
        self.assertEqual(serializer.data['issuer'], contract.issuer.email)
        self.assertEqual(serializer.data['blob']['url'], contract.blob.url)
        self.assertEqual(serializer.data['datetime_created'],
                         contract.datetime_created.strftime(datetime_format))

    def test_serialize_contract_data_for_existing_blob(self):
        from ..models import Contract
        from ..serializers import ContractForm
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create(user=issuer, key=FIX_KEY_PNG)
        data = {'issuer': issuer.pk, 'blob': blob.key, 'name': 'blue'}
        request = HttpRequest()
        request.user = issuer
        serializer = ContractForm(data=data,
                                  context={'request': request})
        serializer_is_valid = serializer.is_valid()
        self.assertTrue(serializer_is_valid)
        serializer.save()
        contract = Contract.objects.get(id=serializer.data['id'])
        self.assertEqual(contract.issuer, issuer)
        self.assertEqual(contract.blob, blob)

    @unittest.skip('not sure if it needs to be covered')
    def test_serialize_contract_data_for_non_existing_blob(self):
        raise NotImplementedError


class ContractAgreementSerializerTests(TestCase):
    def _create_contract(self):
        from ..models import Contract
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        blob = OtherData.objects.create(user=issuer, key=FIX_KEY_PNG)
        return Contract.objects.create(issuer=issuer, blob=blob)

    def test_basic_deserialization(self):
        from ..models import ContractAgreement
        from ..serializers import ContractAgreementSerializer
        # datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        contract = self._create_contract()
        contract_agreement = ContractAgreement(signee=signee, contract=contract)
        serializer = ContractAgreementSerializer(contract_agreement)
        self.assertIn('id', serializer.data)
        self.assertIn('contract', serializer.data)
        self.assertIn('appendix', serializer.data)
        self.assertIn('signee', serializer.data)
        self.assertIn('datetime_deleted', serializer.data)
        self.assertIn('datetime_accepted', serializer.data)
        self.assertIn('datetime_rejected', serializer.data)
        self.assertEqual(serializer.data['id'], contract_agreement.pk)
        self.assertEqual(serializer.data['contract']['id'],
                         contract_agreement.contract.pk)
        self.assertEqual(serializer.data['appendix'],
                         contract_agreement.appendix)
        self.assertEqual(serializer.data['signee'], contract_agreement.signee.username)
        self.assertEqual(serializer.data['datetime_deleted'],
                         contract_agreement.datetime_deleted)
        self.assertEqual(serializer.data['datetime_accepted'],
                         contract_agreement.datetime_accepted)
        self.assertEqual(serializer.data['datetime_rejected'],
                         contract_agreement.datetime_rejected)

    def test_serialize_contract_agreement_data(self):
        from ..models import ContractAgreement
        from ..serializers import ContractAgreementForm

        contract = self._create_contract()
        signee = User.objects.create(username='signee', email='signee@xyz.ct')
        data = {'contract': contract.pk, 'signee': signee.email}
        request = HttpRequest()
        request.user = contract.issuer
        serializer = ContractAgreementForm(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        contract_agreement = ContractAgreement.objects.get(id=serializer.data['id'])
        self.assertEqual(contract_agreement.signee, signee)
        self.assertEqual(contract_agreement.contract, contract)
        self.assertEqual(contract_agreement.datetime_deleted, None)
        self.assertEqual(contract_agreement.datetime_accepted, None)
        self.assertEqual(contract_agreement.datetime_rejected, None)

    @unittest.skip('not yet implemented')
    def test_deserialize_contract_with_datetimes(self):
        raise NotImplementedError

    def test_deserialize_contract_agreement_with_appendix(self):
        from ..models import Contract, ContractAgreement
        from ..serializers import ContractAgreementForm
        from blobs.models import OtherData
        from users.models import User

        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        signee = User.objects.create(username='signee', email='signee@abc.io')
        blob = OtherData.objects.create(user=issuer)
        appendix = {'text': 'xyx'}
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        contract_agreement = ContractAgreement.objects.create(
            signee=signee,
            contract=contract,
            appendix=appendix
        )
        serializer = ContractAgreementForm(contract_agreement)
        self.assertEqual(serializer.data['appendix'],
                         contract_agreement.appendix)

    def test_serialize_contract_agreement_data_with_appendix(self):
        from ..models import Contract, ContractAgreement
        from ..serializers import ContractAgreementForm
        from blobs.models import OtherData
        # TODO use fixtures insread once moved to pytest
        FIX_KEY_PNG = 'ascribe_spiral.png'

        issuer = User.objects.create(username='issuer', email='issuer@abc.io')
        signee = User.objects.create(username='signee', email='signee@abc.io')
        blob = OtherData.objects.create(user=issuer, key=FIX_KEY_PNG)
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        data = {
            'signee': signee.email,
            'contract': contract.pk,
            'appendix': {'text': 'xyx'},
        }
        request = HttpRequest()
        request.user = issuer
        serializer = ContractAgreementForm(data=data,
                                           context={'request': request})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        contract_agreement = ContractAgreement.objects.get(id=serializer.data['id'])
        self.assertEqual(contract_agreement.appendix, data['appendix'])


class SharePieceSerializerTests(TestCase):

    def test_deserialization_without_message(self):
        from ..serializers import SharePieceModalForm
        from dynamicfixtures import _alice, _bob, _piece
        alice = _alice()
        bob = _bob()
        piece = _piece()
        data = {'share_emails': bob.email, 'piece_id': piece.pk}
        request = HttpRequest()
        request.user = alice
        serializer = SharePieceModalForm(data=data,
                                         context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['share_message'], '')

    def test_deserialization_with_blank_message(self):
        from ..serializers import SharePieceModalForm
        from dynamicfixtures import _alice, _bob, _piece
        alice = _alice()
        bob = _bob()
        piece = _piece()
        data = {
            'share_emails': bob.email,
            'share_message': '',
            'piece_id': piece.pk,
        }
        request = HttpRequest()
        request.user = alice
        serializer = SharePieceModalForm(data=data,
                                         context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['share_message'], '')

    def test_deserialization_with_none_message(self):
        from ..serializers import SharePieceModalForm
        from dynamicfixtures import _alice, _bob, _piece
        alice = _alice()
        bob = _bob()
        piece = _piece()
        data = {
            'share_emails': bob.email,
            'share_message': None,
            'piece_id': piece.pk,
        }
        request = HttpRequest()
        request.user = alice
        serializer = SharePieceModalForm(data=data,
                                         context={'request': request})
        self.assertFalse(serializer.is_valid())
