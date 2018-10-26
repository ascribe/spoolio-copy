from django.apps import AppConfig
from django.db.models.signals import post_migrate

from django.conf import settings


class BitcoinAppConfig(AppConfig):
    name = 'bitcoin'

    def ready(self):
        from bitcoin import signals

        if not settings.TESTING:
            post_migrate.connect(signals.check_pubkey, sender=self)
