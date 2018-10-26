from django.dispatch import Signal

# custom signal to be sent after a safe_delete
safe_delete = Signal(providing_args=["instance"])

share_delete = Signal(providing_args=["user"])

# custom signal to be sent when trying to transfer to a user that needs to register
transfer_user_needs_to_register = Signal(providing_args=["prev_owner", "edition"])

# custom signal to be sent when a consignment is confirmed
consignment_confirmed = Signal(providing_args=["instance"])

# custom signal to be sent when a consignment is denied
consignment_denied = Signal(providing_args=["prev_owner", "new_owner", "edition"])

# custom signal to be sent when a consignment is withdrawn
consignment_withdraw = Signal(providing_args=["prev_owner", "new_owner", "edition"])

# custom signal to be sent when an unconsignment is created
unconsignment_create = Signal(providing_args=["instance", "password"])


# custom signal to be sent when a loan edition is created
# we use this signal instead of the post_save on LoanEdition
# when we need access to the user password
loan_edition_created = Signal(providing_args=["instance", "password"])


# custom signal to be sent when a loan on an edition is confirmed
loan_edition_confirm = Signal(providing_args=["instance"])


# custom signal to be sent when a loan piece is created
# we use this signal instead of the post_save on LoanPiece
# when we need access to the user password
loan_piece_created = Signal(providing_args=["instance", "password"])


# custom signal to be sent when a loan on a piece is confirmed
loan_piece_confirm = Signal(providing_args=["instance"])

# custom signal to be sent when a transfer is created
# we use this signal instead of the post_save on OwnershipTransfer
# when we need access to the user password
transfer_created = Signal(providing_args=["instance", "password"])

# custom signal to be sent when a consignment is created
# we use this signal instead of the post_save on Consignment
# when we need access to the user password
consignment_created = Signal(providing_args=["instance", "password"])
