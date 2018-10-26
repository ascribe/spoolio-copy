from rest_framework import serializers


class VerifyCoaForm(serializers.Serializer):
    message = serializers.CharField(max_length=200, required=True)
    signature = serializers.CharField(max_length=600, required=True)
