from rest_framework import serializers
from ownership.models import Contract


class ContractRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, obj):
        from ownership.serializers import ContractSerializer
        contract = Contract.objects.get(pk=obj.pk)
        return ContractSerializer(contract).data
