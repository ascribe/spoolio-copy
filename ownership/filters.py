import django_filters

from .models import Contract, ContractAgreement
from core.filters import BooleanFilter


class ContractFilter(django_filters.FilterSet):
    is_active = BooleanFilter()
    is_public = BooleanFilter()
    issuer = django_filters.CharFilter(name='issuer__email')

    class Meta:
        model = Contract


class ContractAgreementFilter(django_filters.FilterSet):
    accepted = BooleanFilter(
        name='datetime_accepted',
        lookup_type='isnull',
        exclude=True,
    )
    rejected = BooleanFilter(
        name='datetime_rejected',
        lookup_type='isnull',
        exclude=True
    )
    issuer = django_filters.CharFilter(name='contract__issuer__email')

    class Meta:
        model = ContractAgreement
