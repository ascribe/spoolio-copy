from django.dispatch import Signal

# custom signal to be sent after the bulk_create of editions
# since bulk_create does not send signals
editions_bulk_create = Signal(providing_args=["user_registered", "editions"])
