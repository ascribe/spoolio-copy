from acl.models import ActionControl
from blobs.models import DigitalWork, OtherData, Thumbnail
from rest_framework import serializers
from piece.models import Piece


class FileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.CharField()
    url_safe = serializers.CharField()
    mime = serializers.CharField()


class FileForm(serializers.ModelSerializer):
    def validate(self, attrs):
        attrs['user'] = self.context.get('request').user
        return attrs


class DigitalWorkForm(FileForm):
    class Meta:
        model = DigitalWork
        exclude = ('digital_work_hash',)


class DigitalWorkDeleteForm(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context.get('request')
        try:
            digitalwork_to_delete = DigitalWork.objects.get(user=request.user,
                                                            id=self.initial_data['id'])
        except DigitalWork.DoesNotExist:
            raise serializers.ValidationError('Digital work with the given key does not exist')
        piece = Piece.objects.filter(digital_work_id=digitalwork_to_delete.id,
                                     user_registered_id=self.context['request'].user,
                                     datetime_deleted=None)
        if piece:
            raise serializers.ValidationError('Piece already registered, '
                                              'you cannot change the digital work')
        return digitalwork_to_delete

    class Meta:
        model = DigitalWork
        fields = ('id',)


class DigitalWorkSerializer(FileSerializer):
    hash = serializers.CharField()
    encoding_urls = serializers.ListField()
    isEncoding = serializers.IntegerField()


class ThumbnailForm(FileForm):
    class Meta:
        model = Thumbnail
        fields = ('thumbnail_file',)


class ThumbnailDeleteForm(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context.get('request')
        try:
            thumbnail_to_delete = Thumbnail.objects.get(user=request.user,
                                                        id=self.initial_data['id'])
        except Thumbnail.DoesNotExist:
            raise serializers.ValidationError('Thumbnail with the given key does not exist')
        piece = Piece.objects.filter(thumbnail_id=thumbnail_to_delete.id,
                                     user_registered_id=self.context['request'].user,
                                     datetime_deleted=None)
        if piece:
            raise serializers.ValidationError('Piece already registered, '
                                              'you cannot change the thumbnail')
        return thumbnail_to_delete

    class Meta:
        model = Thumbnail
        fields = ('id',)


class ThumbnailSerializer(FileSerializer):
    thumbnail_sizes = serializers.DictField()


class OtherDataForm(FileForm):
    def validate(self, data):
        data = super(OtherDataForm, self).validate(data)
        from piece.serializers import get_piece_or_raise_error
        if 'piece_id' not in self.initial_data:
            raise serializers.ValidationError({'piece_id': 'Please provide a valid piece_id'})
        piece = get_piece_or_raise_error(self.initial_data['piece_id'])
        self._validate_acl(piece)
        return data

    def _validate_acl(self, piece):
        try:
            if not piece.acl(self.context["request"].user).acl_edit:
                raise serializers.ValidationError("You don't have the appropriate rights to edit this field")
        except ActionControl.DoesNotExist:
            raise serializers.ValidationError("You don't have the appropriate rights to edit this field")

    class Meta:
        model = OtherData
        fields = ('other_data_file',)


class OtherDataDeleteForm(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context.get('request')
        try:
            otherdata_to_delete = OtherData.objects.get(user=request.user,
                                                        id=self.initial_data['id'])
        except OtherData.DoesNotExist:
            raise serializers.ValidationError('Data with the given key does not exist')
        return otherdata_to_delete

    class Meta:
        model = OtherData
        fields = ('id',)


class ContractBlobForm(FileForm):
    class Meta:
        model = OtherData
        fields = ('other_data_file',)
