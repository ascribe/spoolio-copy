import logging
from django.db import models

logger = logging.getLogger(__name__)


class WebhookModel(models.Model):

    webhook_event = None

    class Meta:
        abstract = True

    @property
    def webhook_data(self):
        return None

    def send_webhook(self, user):
        try:
            # models can also have custom defined events
            from webhooks.signals import webhook_event

            webhook_event.send(
                sender=self.__class__,
                event_name=self.webhook_event,
                instance=self,
                user=user
            )
        except Exception as e:
            logger.info('Error on webhook:\n{}'.format(e.message))

    def serialize_hook(self, hook):
        # optional, there are serialization defaults
        # we recommend always sending the Hook
        # metadata along for the ride as well
        return {
            'hook': hook.dict(),
            'data': self.webhook_data
        }