from __future__ import absolute_import

from rest_framework.test import APIRequestFactory, force_authenticate
from blobs.models import OtherData

from ownership.api import LoanPieceEndpoint, TransferEndpoint, ConsignEndpoint, UnConsignEndpoint
from ownership.api import LoanEndpoint, ShareEndpoint, SharePieceEndpoint
from ownership.models import Contract, ContractAgreement


class APIUtilTransfer(object):
    factory = APIRequestFactory()

    def create_transfer(self, transferer, transferee_email, edition_bitcoin_id, password):
        data = {'transferee': transferee_email,
                'bitcoin_id': edition_bitcoin_id,
                'password': password}

        view = TransferEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/transfers/', data)
        force_authenticate(request, user=transferer)

        response = view(request)
        return response

    def withdraw_transfer(self, transferer, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = TransferEndpoint.as_view({'post': 'withdraw'})
        request = self.factory.post('/api/ownership/transfers/', data)
        force_authenticate(request, transferer)

        response = view(request)
        return response


class APIUtilConsign(object):
    factory = APIRequestFactory()

    def create_consign(self, consigner, consignee_email, edition_bitcoin_id, password, contract_agreement_id=None):
        data = {'consignee': consignee_email,
                'bitcoin_id': edition_bitcoin_id,
                'password': password}

        if contract_agreement_id:
            data.update({'contract_agreement_id': contract_agreement_id})

        view = ConsignEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/consigns/', data)
        force_authenticate(request, user=consigner)

        response = view(request)
        return response

    def confirm_consign(self, consignee, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = ConsignEndpoint.as_view({'post': 'confirm'})
        request = self.factory.post('/api/ownership/consigns/', data)
        force_authenticate(request, user=consignee)

        response = view(request)
        return response

    def deny_consign(self, consignee, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = ConsignEndpoint.as_view({'post': 'deny'})
        request = self.factory.post('/api/ownership/consigns/', data)
        force_authenticate(request, user=consignee)

        response = view(request)
        return response

    def withdraw_consign(self, consigner, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = ConsignEndpoint.as_view({'post': 'withdraw'})
        request = self.factory.post('/api/ownership/consigns/', data)
        force_authenticate(request, user=consigner)

        response = view(request)
        return response


class APIUtilUnconsign(object):
    factory = APIRequestFactory()

    def create_unconsign(self, consignee, edition_bitcoin_id, password):
        data = {'bitcoin_id': edition_bitcoin_id,
                'password': password}

        view = UnConsignEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/unconsigns/', data)
        force_authenticate(request, user=consignee)

        response = view(request)
        return response

    def request_unconsign(self, user, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = UnConsignEndpoint.as_view({'post': 'request'})
        request = self.factory.post('/api/ownership/unconsigns/request/', data)
        force_authenticate(request, user)

        response = view(request)
        return response


class APIUtilLoanPiece(object):
    factory = APIRequestFactory()

    def create_loan_piece(self, loaner, loanee_email, piece_id, startdate, enddate, password,
                          contract_agreement_id=None):
        data = {
            'loanee': loanee_email,
            'piece_id': piece_id,
            'startdate': startdate,
            'enddate': enddate,
            'password': password,
            'terms': True
        }

        if contract_agreement_id:
            data.update({'contract_agreement_id': contract_agreement_id})

        view = LoanPieceEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/loans/pieces/', data)
        force_authenticate(request, user=loaner)

        response = view(request)
        return response

    def confirm_loan_piece(self, loanee, piece_id):
        data = {
            'piece_id': piece_id
        }

        view = LoanPieceEndpoint.as_view({'post': 'confirm'})
        request = self.factory.post('/api/ownership/loans/pieces/', data)
        force_authenticate(request, user=loanee)

        response = view(request)
        return response

    def deny_loan_piece(self, loanee, piece_id):
        data = {
            'piece_id': piece_id
        }

        view = LoanPieceEndpoint.as_view({'post': 'deny'})
        request = self.factory.post('/api/ownership/loans/pieces/', data)
        force_authenticate(request, user=loanee)

        response = view(request)
        return response

    def request_loan_piece(self, loanee, piece_id, startdate, enddate):
        data = {
            'piece_id': piece_id,
            'startdate': startdate,
            'enddate': enddate,
            'terms': True,
        }

        view = LoanPieceEndpoint.as_view({'post': 'request'})
        request = self.factory.post('/api/ownership/loans/pieces/request/', data)
        force_authenticate(request, user=loanee)

        response = view(request)
        return response

    def request_confirm_loan_piece(self, loanee, piece_id, password):
        data = {
            'piece_id': piece_id,
            'password': password,
        }

        view = LoanPieceEndpoint.as_view({'post': 'request_confirm'})
        request = self.factory.post('/api/ownersip/loans/pieces/request_confirm/', data)
        force_authenticate(request, user=loanee)

        response = view(request)
        return response


class APIUtilLoanEdition(object):
    factory = APIRequestFactory()

    def create_loan_edition(self, loaner, loanee_email, edition_bitcoin_id, startdate, enddate, password):
        data = {'loanee': loanee_email,
                'bitcoin_id': edition_bitcoin_id,
                'startdate': startdate,
                'enddate': enddate,
                'password': password,
                'terms': True}

        view = LoanEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/loans/editions/', data)
        force_authenticate(request, user=loaner)

        response = view(request)
        return response

    def confirm_loan_edition(self, loanee, edition_bitcoin_id):
        data = {'bitcoin_id': edition_bitcoin_id}

        view = LoanEndpoint.as_view({'post': 'confirm'})
        request = self.factory.post('/api/ownership/loans/editions/confirm/', data)
        force_authenticate(request, user=loanee)

        response = view(request)
        return response


class APIUtilShareEdition(object):
    factory = APIRequestFactory()

    def create_share_edition(self, sharer, sharee_email, edition_bitcoin_id):
        data = {'share_emails': sharee_email,
                'bitcoin_id': edition_bitcoin_id}

        view = ShareEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/shares/editions/', data)
        force_authenticate(request, user=sharer)

        response = view(request)
        return response

    def delete_share_edition(self, sharee, edition_bitcoin_id):
        view = ShareEndpoint.as_view({'delete': 'delete'})
        request = self.factory.delete('/api/ownership/shares/editions/')
        force_authenticate(request, user=sharee)

        response = view(request, pk=edition_bitcoin_id)
        return response


class APIUtilSharePiece(object):
    factory = APIRequestFactory()

    def create_share_piece(self, sharer, sharee_email, piece_id):
        data = {'share_emails': sharee_email,
                'piece_id': piece_id}

        view = SharePieceEndpoint.as_view({'post': 'create'})
        request = self.factory.post('/api/ownership/shares/pieces/', data)
        force_authenticate(request, user=sharer)

        response = view(request)
        return response

    def delete_share_piece(self, sharee, piece_id):
        view = SharePieceEndpoint.as_view({'delete': 'delete'})
        request = self.factory.delete('/api/ownership/shares/pieces/')
        force_authenticate(request, user=sharee)

        response = view(request, pk=piece_id)
        return response


class APIUtilContractAgreement(object):

    def create_contractagreement(self, issuer, signee):
        blob = OtherData.objects.create()
        contract = Contract.objects.create(issuer=issuer, blob=blob)
        contract_agreement = ContractAgreement.objects.create(contract=contract,
                                                              signee=signee)
        return contract_agreement
