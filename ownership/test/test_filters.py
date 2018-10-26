from __future__ import absolute_import

from datetime import datetime

import pytz

from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import TestCase


class ContractAgreementFilterTests(TestCase):

    def test_accepted_True(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        accepted_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('accepted=True')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 1)
        self.assertEqual(contract_agreement_filter.qs.get(),
                         accepted_contract_agreement)

    def test_accepted_true(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        accepted_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('accepted=true')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 1)
        self.assertEqual(contract_agreement_filter.qs.get(),
                         accepted_contract_agreement)

    def test_accepted_False(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        accepted_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('accepted=False')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs.distinct()), 2)
        self.assertNotIn(accepted_contract_agreement,
                         contract_agreement_filter.qs)

    def test_accepted_false(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        accepted_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_accepted=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('accepted=false')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs.distinct()), 2)
        self.assertNotIn(accepted_contract_agreement,
                         contract_agreement_filter.qs)

    def test_rejected_True(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        rejected_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('rejected=True')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 1)
        self.assertEqual(contract_agreement_filter.qs.get(),
                         rejected_contract_agreement)

    def test_rejected_true(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        rejected_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('rejected=true')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 1)
        self.assertEqual(contract_agreement_filter.qs.get(),
                         rejected_contract_agreement)

    def test_rejected_False(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        rejected_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('rejected=False')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 2)
        self.assertNotIn(rejected_contract_agreement,
                         contract_agreement_filter.qs)

    def test_rejected_false(self):
        from ..models import Contract, ContractAgreement
        from ..filters import ContractAgreementFilter
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
        rejected_contract_agreement = ContractAgreement.objects.create(
            signee=alice,
            contract=contract,
            datetime_rejected=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )

        data = QueryDict('rejected=false')
        queryset = ContractAgreement.objects.all()
        contract_agreement_filter = ContractAgreementFilter(data=data,
                                                            queryset=queryset)
        self.assertEqual(len(contract_agreement_filter.qs), 2)
        self.assertNotIn(rejected_contract_agreement,
                         contract_agreement_filter.qs)
