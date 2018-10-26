# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
def forwards_func(apps, schema_editor):

    LoanPiece = apps.get_model('ownership', 'LoanPiece')
    ContractAgreement = apps.get_model('ownership', 'ContractAgreement')
    Contract = apps.get_model('ownership', 'Contract')
    OtherData = apps.get_model('blobs', 'OtherData')
    for contract in OtherData.objects.filter(other_data_file__contains="/contract/").order_by("-id"):
        try:
            c = Contract.objects.get(blob=contract,
                                     issuer=contract.user,
                                     is_public=True,
                                     is_active=True,
                                     name="Terms and Conditions")
        except Contract.DoesNotExist:
            c = Contract(blob=contract,
                         issuer=contract.user,
                         is_public=True,
                         is_active=True,
                         name="Terms and Conditions")
            c.save()
    for loan in LoanPiece.objects.all():
        contracts = OtherData.objects.filter(
            user=loan.new_owner,
            other_data_file__contains="whitelabel").order_by("-id")
        ca = None
        if contracts:
            contract = contracts[0]
            try:
                c = Contract.objects.get(blob=contract,
                                         issuer=loan.new_owner,
                                         is_public=True,
                                         is_active=True,
                                         name="Terms and Conditions")
            except Contract.DoesNotExist:
                c = Contract(blob=contract,
                             issuer=loan.new_owner,
                             is_public=True,
                             is_active=True,
                             name="Terms and Conditions")
                c.save()
            try:
                ca = ContractAgreement.objects.get(contract=c,
                                                   signee=loan.prev_owner)
            except ContractAgreement.DoesNotExist:
                ca = ContractAgreement(contract=c,
                                       signee=loan.prev_owner,
                                       datetime_accepted=loan.datetime)
                ca.save()
        loan.contract_agreement = ca
        loan.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ownership', '0026_ownership_contract_agreement'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        )
    ]
