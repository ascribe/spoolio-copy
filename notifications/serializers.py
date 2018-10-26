import logging

from rest_framework import serializers
from ownership.serializers import ContractAgreementSerializer
from piece.serializers import MinimalPieceSerializer, MinimalEditionSerializer


logger = logging.getLogger(__name__)


class NotificationSerializer(serializers.Serializer):
    notification = serializers.SerializerMethodField()

    def get_notification(self, obj):
        try:
            return obj.notification
        except Exception as e:
            logger.exception(e)
            return []


class PieceNotificationSerializer(NotificationSerializer):
    piece = MinimalPieceSerializer()


class EditionNotificationSerializer(NotificationSerializer):
    edition = MinimalEditionSerializer()


class ContractAgreementNotificationSerializer(NotificationSerializer):
    contract_agreement = ContractAgreementSerializer()
