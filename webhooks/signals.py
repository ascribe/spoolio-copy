from django.dispatch import Signal, receiver

# custom signal to be sent after the bulk_create of editions
# since bulk_create does not send signals
from rest_hooks.utils import find_and_fire_hook

webhook_event = Signal(providing_args=["event_name", "instance", "user"])


@receiver(webhook_event, dispatch_uid='instance-custom-webhook')
def custom_action(sender, event_name, instance, user=None, **kwargs):
    """
    Manually trigger a custom action (or even a standard action).
    """
    find_and_fire_hook(event_name, instance, user_override=user)