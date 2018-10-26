from django.db.models import ObjectDoesNotExist

from piece.serializers import BasicPieceSerializer, get_edition_or_raise_error, BasicEditionSerializer, get_piece_or_raise_error
from rest_framework import serializers



class NoteSerializer(serializers.Serializer):
    bitcoin_id = serializers.CharField(write_only=True, required=True)
    note = serializers.CharField(allow_blank=True)

    def validate_bitcoin_id(self, value):
        return get_edition_or_raise_error(value)


class NotePieceSerializer(NoteSerializer):
    id = serializers.CharField(write_only=True, required=True)
    bitcoin_id = serializers.CharField(required=False, read_only=True)

    def validate_id(self, value):
        return get_piece_or_raise_error(value)


class PublicEditionNoteSerializer(NoteSerializer):

    def validate(self, data):
        edition = data['bitcoin_id']
        user = self.context["request"].user
        try:
            if not edition.acl(user).acl_edit or not edition.user_registered == user:
                raise serializers.ValidationError("You don't have the appropriate rights to add a public note")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("You don't have the appropriate rights to add a public note")
        data['bitcoin_id'] = edition
        return data


class PublicPieceNoteSerializer(NotePieceSerializer):

    def validate(self, data):
        piece = data['id']
        user = self.context["request"].user
        try:
            if not piece.acl(user).acl_edit or not piece.user_registered == user:
                raise serializers.ValidationError("You don't have the appropriate rights to add a public note")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("You don't have the appropriate rights to add a public note")
        data['id'] = piece
        return data
