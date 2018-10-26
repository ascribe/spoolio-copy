from rest_framework import serializers

from acl.util import merge_acl_dict_with_object, merge_acl_dicts

from piece.models import Edition
from piece.serializers import (
    BasicPieceSerializer,
    PieceSerializer,
    BasicPieceSerializerWithFirstEdition,
    DetailedEditionSerializer,
    PieceExtraDataForm,
    get_piece_or_raise_error,
)

from users.serializers import WebUserSerializer

from whitelabel.models import WhitelabelSettings
from whitelabel.serializers import (
    get_acl_submit_edition_by_consign,
    WhitelabelSubdomainSerializerMixin,
    get_acl_user_submit_edition_by_consign,
)


class MarketSerializer(serializers.ModelSerializer):

    class Meta:
        model = WhitelabelSettings
        fields = ('name', )


class MarketUserSerializer(WebUserSerializer,
                           WhitelabelSubdomainSerializerMixin):

    acl = serializers.SerializerMethodField()

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}
        acl = get_acl_user_submit_edition_by_consign(obj, whitelabel_settings=self.whitelabel_settings)

        # override the users acl with the whitelabel settings
        return merge_acl_dict_with_object(acl, self.whitelabel_settings)


class MarketBasicPieceSerializer(BasicPieceSerializerWithFirstEdition):

    class Meta(BasicPieceSerializerWithFirstEdition.Meta):
        fields = BasicPieceSerializerWithFirstEdition.Meta.fields + ('extra_data', )


class MarketPieceSerializer(PieceSerializer, MarketBasicPieceSerializer):

    class Meta(PieceSerializer.Meta):
        fields = PieceSerializer.Meta.fields \
            + MarketBasicPieceSerializer.Meta.fields


class MarketBasicEditionSerializer(BasicPieceSerializer,
                                   WhitelabelSubdomainSerializerMixin):

    def get_acl(self, obj):
        if not self.whitelabel_settings:
            return {}

        try:
            acl = get_acl_submit_edition_by_consign(obj, self.request.user,
                                                    whitelabel_settings=self.whitelabel_settings)
            # override the edition acl with the whitelabel settings
            acl = merge_acl_dict_with_object(acl, self.whitelabel_settings)
            # override the edition acl with the whitelabel settings
            user_acl = get_acl_user_submit_edition_by_consign(self.request.user,
                                                              whitelabel_settings=self.whitelabel_settings)
            return merge_acl_dicts(acl, user_acl)
        except Exception:
            return {}

    class Meta(BasicPieceSerializer.Meta):
        model = Edition
        fields = BasicPieceSerializer.Meta.fields + ('edition_number', 'parent')


class MarketDetailedEditionSerializer(DetailedEditionSerializer, MarketBasicEditionSerializer):

    class Meta(DetailedEditionSerializer.Meta):
        fields = DetailedEditionSerializer.Meta.fields \
            + MarketBasicEditionSerializer.Meta.fields


class MarketPieceExtraDataForm(PieceExtraDataForm):

    def validate(self, data):
        data['piece_id'] = get_piece_or_raise_error(data['piece_id'])
        self._validate_acl(data['piece_id'])
        return data

    def _validate_acl(self, piece):
        if not piece.acl(self.context["request"].user).acl_edit:
            raise serializers.ValidationError("You don't have the appropriate rights to edit this field")
