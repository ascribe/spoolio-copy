from rest_framework import serializers

from rest_hooks.models import Hook


class HookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hook
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context.get('request').user
        if Hook.objects.filter(user=user, event=data['event']):
            raise serializers.ValidationError('There is only one webhook per event allowed.')
        return data