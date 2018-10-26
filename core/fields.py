from collections import OrderedDict

from django.db.models import QuerySet
from django.core.validators import EMPTY_VALUES, validate_email

from rest_framework import serializers
from rest_framework.fields import Field

import six


class RelatedFieldMixin(object):
    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated whenever used.
            queryset = queryset.filter(
                **{self.user_field_name: self.context['request'].user}
            )
        return queryset

    @property
    def choices(self):
        return OrderedDict([(six.text_type(getattr(item, self.slug_field)),
                             six.text_type(item))
                            for item in self.get_queryset()])


class SlugRelatedField(serializers.SlugRelatedField, RelatedFieldMixin):
    def __init__(self, **kwargs):
        self.user_field_name = kwargs.pop('user_field_name', 'user')
        super(SlugRelatedField, self).__init__(**kwargs)


class FormToSerializerBooleanField(serializers.BooleanField):
    ''' workaround to convert django form field to serializer form field
    see my issue https://github.com/tomchristie/django-rest-framework/issues/2394
    '''
    TRUE_VALUES = {'t', 'T', 'true', 'True', 'TRUE', '1', 1, True, 'On', 'on', 'ON'}
    FALSE_VALUES = {'f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False, 'Off', 'off', 'OFF'}


class CommaSeparatedEmailField(Field):
    token = ","

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []

        value = [item.strip().lower() for item in value.split(self.token) if item.strip()]

        return list(set(value))

    def to_internal_value(self, value):
        """
        Check that the field contains one or more 'comma-separated' emails
        and normalizes the data to a list of the email strings.
        """
        value = self.to_python(value)

        if value in EMPTY_VALUES and self.required:
            raise serializers.ValidationError(u"This field is required.")

        for email in value:
            try:
                validate_email(email)
            except serializers.ValidationError:
                raise serializers.ValidationError(u"'%s' is not a valid e-mail address." % email)
        return value
