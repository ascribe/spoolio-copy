from blobs.serializers import DigitalWorkSerializer, ThumbnailSerializer
from rest_framework import serializers
from coa.models import CoaFile
from piece.serializers import get_edition_or_raise_error


class CoaForm(serializers.Serializer):
    bitcoin_id = serializers.CharField(min_length=30)

    def validate_bitcoin_id(self, data):
        user = self.context["request"].user
        edition = get_edition_or_raise_error(data)
        if not edition.owner == user:
            raise serializers.ValidationError("Only the owner can create a certificate")
        return edition


class CoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoaFile
        fields = ('coa_file', 'url', 'url_safe')


class CertificateEditionSerializer(serializers.Serializer):
    request_user = None

    title = serializers.CharField()
    artist_name = serializers.CharField()

    edition_number = serializers.IntegerField()
    num_editions = serializers.IntegerField()
    yearAndEdition_str = serializers.CharField()

    bitcoin_id = serializers.CharField()

    owner = serializers.CharField()
    ownership_history = serializers.ListField()

    thumbnail = ThumbnailSerializer()
    digital_work = DigitalWorkSerializer()
