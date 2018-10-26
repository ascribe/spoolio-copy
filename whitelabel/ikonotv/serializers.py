from rest_framework import serializers
from acl.util import merge_acl_dict_with_object, merge_acl_dicts

from piece.serializers import BasicPieceSerializer, PieceSerializer
from users.serializers import WebUserSerializer
from whitelabel.serializers import (
    WhitelabelSubdomainSerializerMixin,
    get_acl_submit_piece_by_loan,
    get_acl_user_submit_piece_by_loan_and_contractagreement
)


class IkonotvUserSerializer(WebUserSerializer,
                            WhitelabelSubdomainSerializerMixin):
    subdomain = 'ikonotv'
    acl = serializers.SerializerMethodField()

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}
        acl = get_acl_user_submit_piece_by_loan_and_contractagreement(obj, whitelabel_settings=self.whitelabel_settings)
        return merge_acl_dict_with_object(acl, self.whitelabel_settings)


class IkonotvBasicPieceSerializer(BasicPieceSerializer,
                                  WhitelabelSubdomainSerializerMixin):
    subdomain = 'ikonotv'

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}

        try:
            acl = get_acl_submit_piece_by_loan(obj, self.request.user, whitelabel_settings=self.whitelabel_settings)
            # override the piece acl with the whitelabel settings
            acl = merge_acl_dict_with_object(acl, self.whitelabel_settings)
            # override the piece acl with the user acls
            user_acl = get_acl_user_submit_piece_by_loan_and_contractagreement(self.request.user,
                                                                               whitelabel_settings=self.whitelabel_settings)
            return merge_acl_dicts(acl, user_acl)
        except Exception as e:
            return {}

    class Meta(BasicPieceSerializer.Meta):
        fields = BasicPieceSerializer.Meta.fields


class IkonotvPieceSerializer(PieceSerializer, IkonotvBasicPieceSerializer):
    class Meta(PieceSerializer.Meta):
        fields = PieceSerializer.Meta.fields + IkonotvBasicPieceSerializer.Meta.fields
