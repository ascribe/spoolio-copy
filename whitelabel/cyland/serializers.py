from rest_framework import serializers

from acl.util import merge_acl_dict_with_object, merge_acl_dicts

from piece.serializers import BasicPieceSerializer, PieceExtraDataForm, get_piece_or_raise_error, PieceSerializer
from users.serializers import WebUserSerializer

from whitelabel.serializers import (
    WhitelabelSubdomainSerializerMixin,
    get_acl_submit_piece_by_loan,
    get_acl_user_submit_piece_by_loan_and_publiccontract
)


class CylandUserSerializer(WebUserSerializer,
                           WhitelabelSubdomainSerializerMixin):
    subdomain = 'cyland'
    acl = serializers.SerializerMethodField()

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}
        acl = get_acl_user_submit_piece_by_loan_and_publiccontract(obj, whitelabel_settings=self.whitelabel_settings)
        return merge_acl_dict_with_object(acl, self.whitelabel_settings)


class CylandBasicPieceSerializer(BasicPieceSerializer,
                                 WhitelabelSubdomainSerializerMixin):
    subdomain = 'cyland'

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}

        try:
            acl = get_acl_submit_piece_by_loan(obj, self.request.user, whitelabel_settings=self.whitelabel_settings)
            # override the edition acl with the whitelabel settings
            acl = merge_acl_dict_with_object(acl, self.whitelabel_settings)
            # override the edition acl with the whitelabel settings
            user_acl = get_acl_user_submit_piece_by_loan_and_publiccontract(self.request.user,
                                                                            whitelabel_settings=self.whitelabel_settings)
            return merge_acl_dicts(acl, user_acl)
        except Exception as e:
            return {}

    class Meta(BasicPieceSerializer.Meta):
        fields = BasicPieceSerializer.Meta.fields + ('extra_data',)


class CylandPieceSerializer(PieceSerializer, CylandBasicPieceSerializer):
    class Meta(PieceSerializer.Meta):
        fields = PieceSerializer.Meta.fields + CylandBasicPieceSerializer.Meta.fields


class CylandPieceExtraDataForm(PieceExtraDataForm):
    def validate(self, data):
        data['piece_id'] = get_piece_or_raise_error(data['piece_id'])
        self._validate_acl(data['piece_id'])
        return data

    def _validate_acl(self, piece):
        acl = get_acl_submit_piece_by_loan(piece, self.context["request"].user, subdomain='cyland')
        if not acl['acl_edit']:
            raise serializers.ValidationError("You don't have the appropriate rights to edit this field")
