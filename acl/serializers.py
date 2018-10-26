from rest_framework import serializers
from acl.models import ActionControl


class ActionControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionControl
        fields = ('piece', 'edition', 'acl_view', 'acl_edit', 'acl_download', 'acl_delete', 'acl_create_editions',
                  'acl_view_editions', 'acl_share', 'acl_unshare', 'acl_transfer', 'acl_withdraw_transfer',
                  'acl_consign', 'acl_withdraw_consign', 'acl_unconsign', 'acl_request_unconsign',
                  'acl_loan', 'acl_loan_request', 'acl_coa')


def _validate_acl(editions, acl, user, message):
    for edition in editions:
        if acl not in edition.acl(user):
            raise serializers.ValidationError(message)
