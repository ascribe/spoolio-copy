from django import forms

import django_filters


class BooleanField(forms.NullBooleanField):
    widget = django_filters.widgets.BooleanWidget


class BooleanFilter(django_filters.Filter):
    field_class = BooleanField
