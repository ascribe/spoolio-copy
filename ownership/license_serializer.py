from rest_framework import serializers
from ownership.models import License


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ('name', 'code', 'organization', 'url')