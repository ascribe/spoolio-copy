from django.contrib.auth.models import AnonymousUser
from django.conf import settings


class PieceNotification(object):
    piece = None
    notification = None

    def __init__(self, notification, piece):
        self.notification = notification
        self.piece = piece

    @staticmethod
    def get_notifications(piece, user):
        if user == AnonymousUser():
            return None
        notifications = []
        loans = piece.loans(user=user, status=None)
        for loan in loans:
            notifications.append({'action': 'loan',
                                  'action_str': 'Pending loan request',
                                  'by': loan.prev_owner.username})
        loan_requests = piece.loans_requests(user=user, status=None)
        for loan_request in loan_requests:
            notifications.append({'action': 'loan_request',
                                  'action_str': 'Pending loan request',
                                  'by': loan_request.new_owner.username})
        return notifications


class EditionNotification(object):
    notification = None
    edition = None

    def __init__(self, notification, edition):
        self.notification = notification
        self.edition = edition

    @staticmethod
    def get_notifications(edition, user):
        if user == AnonymousUser():
            return None
        notifications = []
        if edition.consign_status == settings.PENDING_CONSIGN and edition.consignee == user:
            notifications.append({'action': 'consign',
                                  'action_str': 'Pending consign request',
                                  'by': edition.owner.username})
        if edition.consign_status == settings.PENDING_UNCONSIGN and edition.consignee == user:
            notifications.append({'action': 'unconsign',
                                  'action_str': 'Pending unconsign request',
                                  'by': edition.owner.username})
        loans = edition.loans(user=user, status=None)
        for loan in loans:
            notifications.append({'action': 'loan',
                                  'action_str': 'Pending loan request',
                                  'by': loan.prev_owner.username})
        return notifications


class ContractAgreementNotification(object):
    notification = None
    contract_agreement = None

    def __init__(self, notification, contract_agreement):
        self.notification = notification
        self.contract_agreement = contract_agreement

    @staticmethod
    def get_notifications(contract_agreement, user):
        if user == AnonymousUser():
            return None
        notifications = []
        if contract_agreement.datetime_accepted is None:
            notifications.append({'action': 'contract_agreement',
                                  'action_str': 'Pending contract agreement',
                                  'by': contract_agreement.contract.issuer.username})
        return notifications
