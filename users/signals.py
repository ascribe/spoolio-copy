from django.dispatch import Signal

# custom signal to be sent when an invited user logins for the first time
check_pending_actions = Signal(providing_args=["user"])
