from rest_framework import serializers

from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from oauth2_provider.models import AccessToken, get_application_model

Application = get_application_model()


class ApplicationSerializer(serializers.ModelSerializer):
    bearer_token = serializers.SerializerMethodField()

    def get_bearer_token(self, obj):
        token = AccessToken.objects.get(application=obj)
        return TokenSerializer(token).data

    class Meta:
        model = Application
        fields = ('name', 'client_id', 'client_type', 'authorization_grant_type', 'bearer_token')


class ApplicationForm(serializers.ModelSerializer):
    def validate_name(self, data):
        request = self.context.get('request')
        app = Application.objects.filter(user=request.user, name=data)
        if len(app):
            raise serializers.ValidationError(_('Application with name %s already exists') % data)
        return data

    class Meta:
        model = Application
        fields = ('name',)


class ApplicationTokenRefreshForm(serializers.Serializer):
    name = serializers.CharField(required=True)

    def validate_name(self, data):
        request = self.context.get('request')
        try:
            app = Application.objects.get(user=request.user, name=data)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                _('Application with name %s doesn''t exists or you don''t have access.') % data)
        return app


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ('token', 'expires')
