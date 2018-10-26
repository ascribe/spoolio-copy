import logging
import pytz

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from django.utils.datetime_safe import datetime

from rest_framework import filters, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.response import Response

from bitcoin.models import BitcoinWallet
from blobs.models import OtherData
from core.api import ModelViewSetKpi

from .filters import ContractFilter, ContractAgreementFilter
from ownership.license_serializer import LicenseSerializer
from ownership.models import (
    Contract,
    ContractAgreement,
    OwnershipRegistration,
    OwnershipTransfer,
    OwnershipPiece,
    Consignment,
    UnConsignment,
    Loan,
    LoanPiece,
    LoanDetail,
    Share,
    SharePiece,
    License
)
from ownership.serializers import (
    ContractAgreementSerializer,
    OwnershipPieceSerializer,
    OwnershipEditionSerializer,
    LoanSerializer,
    LoanPieceSerializer,
    TransferModalForm,
    TransferWithdrawForm,
    ConsignModalForm,
    ConsignConfirmSerializer,
    ConsignWithdrawForm,
    UnConsignModalForm,
    UnConsignRequestSerializer,
    UnConsignDenySerializer,
    LoanModalForm,
    LoanDenySerializer,
    LoanPieceModalForm,
    LoanPieceDenySerializer,
    LoanPieceRequestSerializer,
    LoanPieceRequestConfirmSerializer,
    LoanPieceRequestDenySerializer,
    ContractSerializer,
    ContractForm,
    ContractAgreementForm,
    ShareDeleteForm,
    ShareModalForm,
    SharePieceDeleteForm,
    SharePieceModalForm
)
from ownership.signals import (
    transfer_user_needs_to_register,
    consignment_confirmed,
    consignment_denied,
    consignment_withdraw,
    unconsignment_create,
    share_delete,
    loan_edition_confirm,
    loan_piece_confirm,
    transfer_created,
    consignment_created,
    loan_edition_created,
    loan_piece_created
)

from users.api import createOrGetUser
from users.models import UserNeedsToRegisterRole

from util.util import extract_subdomain
from web.api_util import PaginatedGenericViewSetKpi, GenericViewSetKpi
from emails import messages
from emails.tasks import (
    send_ascribe_email,
    email_contract_agreement_decision,
    email_send_contract_agreement,
)
from whitelabel.models import WhitelabelSettings

logger = logging.getLogger(__name__)


# =========================================================================================
# REGISTER
class RegistrationEndpoint(PaginatedGenericViewSetKpi):
    # default queryset. We can override this on the view methods
    queryset = OwnershipRegistration.objects.all()
    # When writing class based views there is no easy way to override the
    # permissions for invidual view methods. The easiest way is to
    # create custom permission classes
    permission_classes = [IsAuthenticatedOrReadOnly]
    json_name = 'registrations'

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        try:
            ownership = queryset.get(pk=pk)
        except queryset.model.DoesNotExist:
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(
                {'success': False, 'reason': 'id of object must be a number'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # NOTE: Unfortunately, the `RegistrationEndpoint` is used as a base class
        #       for a multitude of other Ownership endpoints.
        #       As those either depend on an Edition or a Piece, we need to dynamically
        #       determine their respective serializer.
        if ownership.type in (OwnershipRegistration.__name__,
                              OwnershipPiece.__name__,
                              SharePiece.__name__):
            serializer = OwnershipPieceSerializer
        elif ownership.type == Loan.__name__:
            serializer = LoanSerializer
        elif ownership.type == LoanPiece.__name__:
            serializer = LoanPieceSerializer
        else:
            serializer = OwnershipEditionSerializer

        return Response(
            {'success': True, self.json_name[:-1]: serializer(ownership).data},
            status=status.HTTP_200_OK,
        )

    def get_queryset(self):
        if self.request.user == AnonymousUser():
            return self.queryset.none()
        if self.action in ["list", "retrieve"]:
            return self.queryset.filter(Q(prev_owner=self.request.user)
                                        | Q(new_owner=self.request.user)
                                        & Q(datetime_deleted=None)
                                        & Q(piece__datetime_deleted=None)) \
                .exclude(status=0)
        return self.queryset


# =========================================================================================
# TRANSFER
class TransferEndpoint(RegistrationEndpoint):
    """
    Endpoint for transferring pieces
    """
    queryset = OwnershipTransfer.objects.all()
    json_name = 'transfers'

    def create(self, request):
        """
        Create a Transfer object and push to bitcoin network
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            transferee = createOrGetUser(data['transferee'])
            editions = data['bitcoin_id']
            extra_data = data.get('extra_data')
            for edition in editions:
                transfer_pk = TransferEndpoint._transfer(
                    data['password'], edition, transferee, extra_data)

            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            if subdomain == '23vivi':
                msg_cls = messages.TransferEmailMessage23vivi
            elif subdomain == 'lumenus':
                msg_cls = messages.TransferEmailMessageLumenus
            elif subdomain == 'polline':
                msg_cls = messages.TransferEmailMessagePolline
            elif subdomain == 'artcity':
                msg_cls = messages.TransferEmailMessageArtcity
            elif subdomain == 'demo':
                msg_cls = messages.TransferEmailMessageDemo
            elif subdomain == 'liquidgallery':
                msg_cls = messages.TransferEmailMessageLiquidGallery
            else:
                msg_cls = messages.TransferEmailMessage
            send_ascribe_email.delay(
                msg_cls=msg_cls,
                sender=request.user,
                receiver=transferee,
                editions=editions,
                message=data['transfer_message'],
                subdomain=subdomain,
            )
            msg = 'You have successfully transferred %d edition(s) to %s.' % (len(editions), transferee.email)
            return Response({'success': True,
                             'notification': msg,
                             'transfer_pk': transfer_pk,
                             },
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def withdraw(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            edition = serializer.validated_data['bitcoin_id']
            transfer = serializer.validated_data['transfer']
            transfer.delete()
            edition.pending_new_owner = None
            edition.save()
            # TODO: maybe the user was the registree without this transfer?
            msg = ['You have withdrawn the transfer ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _transfer(password, edition, transferee, extra_data):
        try:
            assert password, "password not provided"
            # if consignment, consignment = dependent tx and consignee is prev_owner
            if edition.consignee:
                prev_owner = edition._most_recent_consignment.new_owner
                prev_btc_address = edition._most_recent_consignment.new_btc_address
            else:
                prev_owner = edition.owner
                prev_btc_address = None

            transfer = OwnershipTransfer.create(
                edition=edition,
                prev_owner=prev_owner,
                transferee=transferee,
                prev_btc_address=prev_btc_address,
            )
            # store the ciphertext_wif
            transfer.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(transfer, password)
            transfer.extra_data = extra_data
            transfer.save()
            transfer_created.send(sender=TransferEndpoint, instance=transfer, password=password)

            if UserNeedsToRegisterRole.objects.filter(
                user=transferee, type='UserNeedsToRegisterRole').exists():
                # new user, store encrypted pwd and transfer later

                edition.pending_new_owner = transferee

                # signal the acl app to set the permissions for this edition
                transfer_user_needs_to_register.send(sender=TransferEndpoint, prev_owner=prev_owner, edition=edition)
            else:
                edition.owner = transferee
                logger.info('piece transferred in DB')

            edition.consignee = None
            edition.consign_status = settings.NOT_CONSIGNED
            edition.save()
            return transfer.pk

        except Exception, e:
            # raise Exception('Bitcoin ownership transfer failed. Error: %s' % e.message)
            logger.exception(e)
            raise

    def get_serializer_class(self):
        if self.action == "create":
            return TransferModalForm
        if self.action == "withdraw":
            return TransferWithdrawForm
        return OwnershipEditionSerializer


# ========================================================================================
# CONSIGN
class ConsignEndpoint(RegistrationEndpoint):
    """
    Endpoint for consigning pieces
    """

    queryset = Consignment.objects.all()
    json_name = 'consignments'

    def create(self, request):
        """
        Create a Consigment object
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            consignee = createOrGetUser(data['consignee'])
            editions = data['bitcoin_id']

            contract_agreement = data['contract_agreement_id']
            if contract_agreement and not contract_agreement.datetime_accepted:
                contract_agreement.datetime_accepted = datetime.utcnow().replace(tzinfo=pytz.UTC)
                contract_agreement.save()

            for edition in editions:
                # update ownership
                consignment = Consignment.create(edition, consignee=consignee, owner=edition.owner)
                consignment.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(consignment,
                                                                                data['password'])

                consignment.contract_agreement = contract_agreement
                consignment.save()

                # send custom signal
                consignment_created.send(sender=ConsignEndpoint, instance=consignment, password=data['password'])

                # update db
                edition.consignee = consignee
                edition.consign_status = settings.PENDING_CONSIGN
                edition.save()
            # send email to consignee: "please confirm"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.ConsignRequestReceiverEmailMessage,
                sender=request.user,
                receiver=consignee,
                editions=editions,
                message=data['consign_message'],
                subdomain=subdomain,
            )
            # send email to owner: "waiting for confirm"
            # TODO for the meantime select the email message class based on the
            # subdomain, this could be pushed to the email message class itself
            # perhaps
            if subdomain == '23vivi':
                msg_cls = messages.ConsignRequestSenderEmailMessage23vivi
            elif subdomain == 'lumenus':
                msg_cls = messages.ConsignRequestSenderEmailMessageLumenus
            elif subdomain == 'polline':
                msg_cls = messages.ConsignRequestSenderEmailMessagePolline
            elif subdomain == 'artcity':
                msg_cls = messages.ConsignRequestSenderEmailMessageArtcity
            elif subdomain == 'demo':
                msg_cls = messages.ConsignRequestSenderEmailMessageDemo
            elif subdomain == 'liquidgallery':
                msg_cls = messages.ConsignRequestSenderEmailMessageLiquidGallery
            else:
                msg_cls = messages.ConsignRequestSenderEmailMessage

            send_ascribe_email.delay(
                msg_cls=msg_cls,
                sender=request.user,
                receiver=consignee,
                editions=editions,
                message=None,
                subdomain=subdomain,
            )

            msg = 'You have successfully consigned %d edition(s), pending their confirmation(s).' \
                  % (len(editions))
            return Response({'success': True, 'notification': msg}, status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            edition = serializer.validated_data['bitcoin_id']
            # update ownership
            consignment = edition._most_recent_consignment
            consignment.setStatus(1)
            consignment.save()

            # signal the acl app to set permissions on the edition
            consignment_confirmed.send(sender=ConsignEndpoint, instance=consignment)

            # update DB
            edition.consign_status = settings.CONSIGNED
            edition.save()
            # send email to owner: "confirmed"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            if subdomain == '23vivi':
                msg_cls = messages.ConsignConfirmSenderEmailMessage23vivi
            elif subdomain == 'lumenus':
                msg_cls = messages.ConsignConfirmSenderEmailMessageLumenus
            elif subdomain == 'polline':
                msg_cls = messages.ConsignConfirmSenderEmailMessagePolline
            elif subdomain == 'artcity':
                msg_cls = messages.ConsignConfirmSenderEmailMessageArtcity
            elif subdomain == 'demo':
                msg_cls = messages.ConsignConfirmSenderEmailMessageDemo
            elif subdomain == 'liquidgallery':
                msg_cls = messages.ConsignConfirmSenderEmailMessageLiquidGallery
            else:
                msg_cls = messages.ConsignConfirmSenderEmailMessage
            send_ascribe_email.delay(
                msg_cls=msg_cls,
                sender=edition.owner,
                receiver=request.user,
                editions=[edition],
                message=None,
                subdomain=subdomain,
            )

            msg = ['You have succesfully confirmed consignment ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def deny(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            edition = serializer.validated_data['bitcoin_id']
            # update ownership
            consignment = edition._most_recent_consignment
            consignment.ciphertext_wif = None
            consignment.setStatus(0)
            consignment.save()
            # update DB
            edition.consignee = None
            edition.consign_status = settings.NOT_CONSIGNED
            edition.save()

            # signal the acl app to set the permissions for the edition
            consignment_denied.send(sender=ConsignEndpoint, prev_owner=consignment.prev_owner,
                                    new_owner=consignment.new_owner, edition=edition)

            # send email to owner: "denied"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            if subdomain == '23vivi':
                msg_cls = messages.ConsignDenySenderEmailMessage23vivi
            elif subdomain == 'lumenus':
                msg_cls = messages.ConsignDenySenderEmailMessageLumenus
            elif subdomain == 'polline':
                msg_cls = messages.ConsignDenySenderEmailMessagePolline
            elif subdomain == 'artcity':
                msg_cls = messages.ConsignDenySenderEmailMessageArtcity
            elif subdomain == 'demo':
                msg_cls = messages.ConsignDenySenderEmailMessageDemo
            elif subdomain == 'liquidgallery':
                msg_cls = messages.ConsignDenySenderEmailMessageLiquidGallery
            else:
                msg_cls = messages.ConsignDenySenderEmailMessage
            send_ascribe_email.delay(
                msg_cls=msg_cls,
                sender=edition.owner,
                receiver=request.user,
                editions=(edition,),
                message=None,
                subdomain=subdomain,
            )

            msg = ['You have denied consignment ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def withdraw(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            edition = serializer.validated_data['bitcoin_id']
            consigment = serializer.validated_data['consigment']

            # signal the acl app to set the permissions of the edition
            consignment_withdraw.send(sender=ConsignEndpoint, prev_owner=consigment.prev_owner,
                                      new_owner=consigment.new_owner, edition=edition)

            consigment.delete()
            edition.consign_status = settings.NOT_CONSIGNED
            edition.consignee = None
            edition.save()
            # TODO: maybe the user was the registree without this consignment?
            msg = ['You have withdrawn the consignment ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "create":
            return ConsignModalForm
        if self.action in ["confirm", "deny"]:
            return ConsignConfirmSerializer
        if self.action == "withdraw":
            return ConsignWithdrawForm
        return OwnershipEditionSerializer


# ========================================================================================
# UNCONSIGN
class UnConsignEndpoint(RegistrationEndpoint):
    """
    Endpoint for consigning pieces
    """

    queryset = UnConsignment.objects.all()
    json_name = 'unconsignments'

    def create(self, request):
        """
        Create a Transfer object and push to bitcoin network
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            consignee = request.user
            editions = data['bitcoin_id']
            for edition in editions:
                # update ownership
                try:
                    unconsignment = UnConsignment.objects.get(edition=edition,
                                                              prev_owner=consignee,
                                                              new_owner=edition.owner,
                                                              status=None)
                except ObjectDoesNotExist as e:
                    unconsignment = UnConsignment.create(edition, owner=edition.owner, consignee=consignee)

                unconsignment.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(unconsignment,
                                                                                  data['password'])

                unconsignment.setStatus(1)
                unconsignment.save()

                # signal acl to set permissions to the edition
                unconsignment_create.send(sender=UnConsignEndpoint, instance=unconsignment, password=data['password'])

                edition._most_recent_consignment.delete_safe()
                # update db
                edition.consignee = None
                edition.consign_status = settings.NOT_CONSIGNED
                edition.save()

                subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                    'HTTP_ORIGIN') else 'www'
                # send email to owner: "FYI piece was unconsigned"
                send_ascribe_email.delay(
                    msg_cls=messages.ConsignTerminateSenderEmailMessage,
                    sender=edition.owner,
                    receiver=consignee,
                    editions=(edition,),
                    message=data['unconsign_message'],
                    subdomain=subdomain,
                )

            msg = 'You have successfully unconsigned %d edition(s).' % (len(editions))

            return Response({'success': True, 'notification': msg}, status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def request(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            edition = data['bitcoin_id']
            # update ownership
            unconsignment = UnConsignment.create(edition, owner=edition.owner, consignee=edition.consignee)
            unconsignment.save()
            # update DB
            edition.consign_status = settings.PENDING_UNCONSIGN
            edition.save()
            # send email to consignee: "please confirm unconsign"

            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.UnconsignmentRequestReceiverEmailMessage,
                sender=edition.owner,
                receiver=edition.consignee,
                editions=[edition],
                message=data['unconsign_request_message'],
                subdomain=subdomain,
            )

            msg = 'You have requested %s to unconsign "%s".' % (edition.consignee.email, edition.title)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def deny(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            edition = data['bitcoin_id']
            # update ownership
            unconsignment = UnConsignment.objects.get(edition=edition,
                                                      prev_owner=edition.consignee,
                                                      new_owner=edition.owner,
                                                      status=None)
            unconsignment.setStatus(0)
            unconsignment.save()
            # update DB
            edition.consign_status = settings.CONSIGNED
            edition.save()
            # send email to owner: "denied"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.UnconsignmentDenySenderEmailMessage,
                sender=edition.owner,
                receiver=request.user,
                editions=[edition],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have denied unconsignment ']
            msg += ['of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "create":
            return UnConsignModalForm
        if self.action == "request":
            return UnConsignRequestSerializer
        if self.action == "deny":
            return UnConsignDenySerializer
        return OwnershipEditionSerializer


# ========================================================================================
# LOAN
class LoanEndpoint(RegistrationEndpoint):
    """
    Endpoint for consigning pieces
    """

    queryset = Loan.objects.all()
    json_name = 'loans'

    def create(self, request):
        """
        Create a Loan object and request the loanee to confirm/deny
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            data = serializer.validated_data

            editions = data['bitcoin_id']
            loanee = createOrGetUser(data['loanee'])
            loan_type = Loan
            startdate = data['startdate']
            enddate = data['enddate']
            gallery = data['gallery']
            loan_message = data['loan_message']
            password = data['password']
            contract_agreement = data['contract_agreement_id']

            for edition in editions:
                loaner = edition.owner
                # LEGACY NOTE:
                # For whatever reason, we're only sending out an email to loaner and loanee with the
                # last loan + all editions attached. Same goes for setting ACLs...
                # Hence, here we're constantly overwriting `loan` to access it after the loop,
                # for sending the emails. We could have used a list comprehension for all loans here,
                # this would however use more memory then needed.
                loan = self._create_loan(edition, loaner, loanee, loan_type, startdate, enddate, gallery,
                                         loan_message, password, contract_agreement)

            self._send_loan_emails(loan.prev_owner, loanee, editions, loan_message, subdomain)
            loan_edition_created.send(sender=LoanEndpoint, instance=loan, password=password)

            msg = 'You have successfully loaned {} edition(s) to {}.'.format(len(editions),
                                                                             loanee.email)
            return Response(
                {
                    'success': True,
                    'notification': msg,
                    'loan': LoanSerializer(loan).data
                },
                status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            edition = data['bitcoin_id']
            # update ownership
            loan = edition.loans(user=request.user, status=None)[0]
            loan.setStatus(1)
            loan.save()
            loan_edition_confirm.send(sender=LoanEndpoint, instance=loan)

            # send email to owner: "loan confirmed"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanConfirmSenderEmailMessage,
                sender=edition.owner,
                receiver=request.user,
                editions=[edition],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have succesfully confirmed the loan ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def deny(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            edition = data['bitcoin_id']
            # update ownership
            loan = edition.loans(user=request.user, status=None)[0]
            loan.setStatus(0)
            loan.ciphertext_wif = None
            loan.save()
            # send email to owner: "denied"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanDenySenderEmailMessage,
                sender=edition.owner,
                receiver=request.user,
                editions=[edition],
                subdomain=subdomain,
            )
            msg = ['You have denied the loan ']
            msg += [' of %s by %s, edition %d.' % (edition.title, edition.artist_name, edition.edition_number)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def _create_loan(self, to_loan, loaner, loanee, loan_type, startdate, enddate, gallery,
                    loan_message, password, contract_agreement=None):
        # If a contract agreement exists and wasn't accepted yet,
        # we accept it as its a precondition to the loan we're yet to create
        if contract_agreement and not contract_agreement.datetime_accepted:
            contract_agreement.datetime_accepted = datetime.utcnow().replace(tzinfo=pytz.UTC)
            contract_agreement.save()

        datetime_from = datetime.combine(startdate, datetime.min.time()).replace(tzinfo=pytz.UTC)
        datetime_to = datetime.combine(enddate, datetime.min.time()).replace(tzinfo=pytz.UTC)

        loan = loan_type.create(to_loan, owner=loaner, loanee=loanee)
        loan.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(loan, password)
        loan.datetime_from = datetime_from
        loan.datetime_to = datetime_to
        loan.contract_agreement = contract_agreement
        loan.save()

        loan_details = LoanDetail(loan=loan, gallery=gallery)
        loan_details.save()

        return loan

    def _send_loan_emails(self, sender, receiver, objs_to_loan, message, subdomain):
        # send email to consignee: "please confirm"
        send_ascribe_email.delay(
            msg_cls=messages.LoanRequestReceiverEmailMessage,
            sender=sender,
            receiver=receiver,
            editions=objs_to_loan,
            message=message,
            subdomain=subdomain,
        )
        # send email to consigner: "waiting for confirm"
        send_ascribe_email.delay(
            msg_cls=messages.LoanRequestSenderEmailMessage,
            sender=sender,
            receiver=receiver,
            editions=objs_to_loan,
            message=None,
            subdomain=subdomain,
        )

    def get_serializer_class(self):
        if self.action == "create":
            return LoanModalForm
        if self.action in ["confirm", "deny"]:
            return LoanDenySerializer
        return LoanSerializer


class LoanPieceEndpoint(LoanEndpoint):
    queryset = LoanPiece.objects.all()

    def create(self, request):
        """
        Create a Loan object and request the loanee to confirm/deny
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            data = serializer.validated_data

            piece = data['piece_id']
            loaner = piece.user_registered
            loanee = createOrGetUser(data['loanee'])
            loan_type = LoanPiece
            startdate = data['startdate']
            enddate = data['enddate']
            gallery = data['gallery']
            loan_message = data['loan_message']
            password = data['password']
            contract_agreement = data['contract_agreement_id']

            loan = super(LoanPieceEndpoint, self)._create_loan(piece, loaner, loanee, loan_type, startdate, enddate,
                                                               gallery, loan_message, password, contract_agreement)
            super(LoanPieceEndpoint, self)._send_loan_emails(loaner, loanee, [piece], loan_message, subdomain)
            loan_piece_created.send(sender=LoanPieceEndpoint, instance=loan, password=password)

            msg = 'You have successfully loaned a piece to {}.'.format(loanee.email)
            return Response(
                {
                    'success': True,
                    'notification': msg,
                    'loan': LoanPieceSerializer(loan).data
                },
                status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            piece = data['piece_id']

            # update ownership
            loan = piece.loans(user=request.user, status=None)[0]
            loan.setStatus(1)
            loan.save()
            loan_piece_confirm.send(sender=LoanPieceEndpoint, instance=loan)

            # send email to owner: "loan confirmed"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanConfirmSenderEmailMessage,
                sender=piece.user_registered,
                receiver=request.user,
                editions=[piece],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have succesfully confirmed the loan ']
            msg += [' of %s by %s.' % (piece.title, piece.artist_name)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def deny(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            piece = data['piece_id']
            # update ownership
            loan = piece.loans(user=request.user, status=None)[0]
            loan.setStatus(0)
            loan.ciphertext_wif = None
            loan.save()
            # send email to owner: "denied"
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanDenySenderEmailMessage,
                sender=piece.user_registered,
                receiver=request.user,
                editions=[piece],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have denied the loan ']
            msg += ['of %s by %s.' % (piece.title, piece.artist_name)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post', 'get'], permission_classes=[IsAuthenticated])
    def request(self, request):
        """
        Create/Get a/all Loan object/s and request the owner of the piece to confirm/deny
        """
        if request.method.lower() == 'post':
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                data = serializer.validated_data

                loanee = request.user
                pieces = data['piece_id']
                contract = None
                if len(data['contract_key']):
                    contract = OtherData.objects.get(other_data_file=data['contract_key'])
                datetime_from = datetime.combine(data['startdate'], datetime.min.time()).replace(tzinfo=pytz.UTC)
                datetime_to = datetime.combine(data['enddate'], datetime.min.time()).replace(tzinfo=pytz.UTC)
                subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if 'HTTP_ORIGIN' in request.META else 'www'
                for piece in pieces:
                    # update ownership
                    loan = LoanPiece.create(piece,
                                            loanee,
                                            owner=piece.user_registered)
                    loan.datetime_from = datetime_from
                    loan.datetime_to = datetime_to
                    loan.save()
                    loan_details = LoanDetail(loan=loan, gallery=data['gallery'], contract_model=contract)
                    loan_details.save()
                    # send email to owner of the piece: "please confirm"
                    # TODO should this be outside the loop?
                    # If there are multiple pieces, multiple identical emails
                    # will be sent ...
                    send_ascribe_email.delay(
                        msg_cls=messages.LoanPieceRequestSenderEmailMessage,
                        sender=piece.user_registered,
                        receiver=loanee,
                        editions=pieces,
                        message=data['loan_message'],
                        subdomain=subdomain,
                    )
                # send email to user that made the loan request: "waiting for confirm"
                send_ascribe_email.delay(
                    msg_cls=messages.LoanPieceRequestReceiverEmailMessage,
                    sender=piece.user_registered,
                    receiver=loanee,
                    editions=pieces,
                    message=None,
                    subdomain=subdomain,
                )
                msg = 'You have successfully requested loan of %d pieces(s), pending their confirmation.' \
                      % (len(pieces))

                return Response({'success': True, 'notification': msg}, status=status.HTTP_201_CREATED)
            else:
                return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            queryset = LoanPiece.objects.filter(prev_owner=request.user, status=None).order_by("datetime")
            if len(queryset):
                serializer = self.get_serializer(queryset, many=True)
                return Response({'success': True, 'loan_requests': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def request_confirm(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            piece = data['piece_id']
            # update ownership
            loan = piece.loans_requests(user=request.user, status=None)[0]
            loan.ciphertext_wif = BitcoinWallet.encoded_wif_for_path(loan, data['password'])
            loan.setStatus(1)
            loan.save()

            # we need to send the loan_piece_created signal here because its the first time we have the
            # password for this ownership object and we need to check if it requires migrations.
            # Maybe there can be a race condition in this case
            loan_piece_created.send(sender=LoanPieceEndpoint, instance=loan, password=data['password'])

            loan_piece_confirm.send(sender=LoanPieceEndpoint, instance=loan)

            # send email to loanee: "loan confirmed"
            loanee = loan.new_owner

            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key('HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanPieceConfirmReceiverEmailMessage,
                sender=piece.user_registered,
                receiver=loanee,
                editions=[piece],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have succesfully confirmed the loan ']
            msg += [' of %s by %s.' % (piece.title, piece.artist_name)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def request_deny(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            piece = data['piece_id']
            # update ownership
            loan = piece.loans_requests(user=request.user, status=None)[0]
            loan.setStatus(0)
            loan.ciphertext_wif = None
            loan.save()
            # send email to owner: "denied"
            loanee = loan.new_owner
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                'HTTP_ORIGIN') else 'www'
            send_ascribe_email.delay(
                msg_cls=messages.LoanPieceDenyReceiverEmailMessage,
                sender=piece.user_registered,
                receiver=loanee,
                editions=[piece],
                message=None,
                subdomain=subdomain,
            )
            msg = ['You have denied the loan ']
            msg += ['of %s by %s.' % (piece.title, piece.artist_name)]
            msg = ''.join(msg)
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "create":
            return LoanPieceModalForm
        if self.action in ["confirm", "deny"]:
            return LoanPieceDenySerializer
        if self.action == "request":
            return LoanPieceRequestSerializer
        if self.action == 'request_confirm':
            return LoanPieceRequestConfirmSerializer
        if self.action == 'request_deny':
            return LoanPieceRequestDenySerializer
        return LoanPieceSerializer


# ========================================================================================
# CONTRACT, CONTRACT AGREEMENT
class ContractEndpoint(ModelViewSetKpi):
    """
    Endpoint for ``Contract`` objects.

    Filters: ``is_active``,  ``is_public``

    For example, to list contracts that are active and private:

        GET /api/ownership/contracts/?is_active=True&is_public=False

    """
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ContractFilter
    json_name = 'contracts'

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return ContractForm
        return ContractSerializer

    def get_queryset(self):
        if 'issuer' in self.request.query_params:
            return Contract.objects.filter(issuer__email=self.request.query_params['issuer'],
                                           is_public=True,
                                           datetime_deleted=None)
        return Contract.objects.filter(issuer=self.request.user,
                                       datetime_deleted=None)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        response = super(ContractEndpoint, self).create(self.request, serializer.validated_data)
        response.status_code = status.HTTP_200_OK
        return response

    def destroy(self, request, *args, **kwargs):
        response = super(ContractEndpoint, self).destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response({'success': True,
                             'notification': 'Contract deleted'}, status=status.HTTP_200_OK)
        else:
            return response

    def perform_destroy(self, instance):
        data = {'datetime_deleted': datetime.utcnow().replace(tzinfo=pytz.UTC)}
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Contract.objects.filter(pk=instance.pk).deactivate()

    @detail_route()
    def pending(self, request, pk=None):
        """
        Lists contracts that have pending ContractAgreement objects, for the given signee.

        """
        contracts = (
            self.get_queryset()
                .filter(contractagreement__signee__pk=pk)
                .exclude(Q(contractagreement__datetime_accepted__isnull=False) |
                         Q(contractagreement__datetime_rejected__isnull=False),
                         contractagreement__datetime_created__isnull=True)
                .distinct()
        )
        serializer = self.get_serializer(contracts, many=True)
        return Response(serializer.data)


class ContractAgreementEndpoint(ModelViewSetKpi):
    """
    Endpoint for ``ContractAgreement`` objects, for both issuers & signees.

    """
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = ContractAgreementFilter
    ordering_fields = ('datetime_accepted', 'datetime_created')
    ordering = ('-datetime_accepted', '-datetime_created')
    json_name = 'contractagreements'

    def get_serializer_class(self):
        if self.action in ['create', 'accept', 'reject']:
            return ContractAgreementForm
        return ContractAgreementSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ContractAgreement.objects.filter(Q(signee=user) |
                                                    Q(contract__issuer=user),
                                                    datetime_deleted__isnull=True)
        pending = self.request.query_params.get('pending', False)
        if pending:
            queryset = queryset.pending()
        return queryset

    # The implicit methods (list, create, retrieve, update, destroy), implemented
    # by django rest framework (ModelViewSet via the mixins), are provided here,
    # to give an explicit entrypoint of the supported functionalities. Removing
    # them shouldn't cause problems.
    def create(self, request, *args, **kwargs):
        return super(ContractAgreementEndpoint, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        contract_agreement = serializer.save()
        user = contract_agreement.signee
        contract = contract_agreement.contract
        subdomain = extract_subdomain(self.request.META['HTTP_ORIGIN']) \
            if self.request.META.has_key('HTTP_ORIGIN') else 'www'

        if not contract.is_public:
            email_send_contract_agreement.apply_async((user, subdomain))

    def retrieve(self, request, *args, **kwargs):
        return super(ContractAgreementEndpoint, self).retrieve(request,
                                                               *args,
                                                               **kwargs)

    def update(self, request, *args, **kwargs):
        return super(ContractAgreementEndpoint, self).update(request,
                                                             *args,
                                                             **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super(ContractAgreementEndpoint, self).destroy(request,
                                                              *args,
                                                              **kwargs)

    @list_route()
    def pending(self, request):
        queryset = self.get_queryset().pending()

        # Here, it's just a replication of what the rest_framework does in its
        # standard list method. All we needed was the filtered query set above.
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def accept(self, request, pk=None):
        response, instance = self._update_datetime_field('datetime_accepted')
        email_contract_agreement_decision.apply_async((instance, True))
        return response

    @detail_route(methods=['put'])
    def reject(self, request, pk=None):
        response, instance = self._update_datetime_field('datetime_rejected')
        email_contract_agreement_decision.apply_async((instance, False))
        return response

    def _update_datetime_field(self, field_name):
        instance = self.get_object()
        data = {field_name: datetime.utcnow().replace(tzinfo=pytz.UTC)}
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data), instance


# =========================================================================================
# SHARE
class ShareEndpoint(RegistrationEndpoint):
    queryset = Share.objects.all()
    json_name = 'shares'

    def create(self, request):
        """
        Send an email with the public URL
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            editions = data['bitcoin_id']
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key('HTTP_ORIGIN') else 'www'
            ShareEndpoint._share_and_email(request.user,
                                           editions,
                                           data['share_emails'],
                                           data['share_message'],
                                           subdomain=subdomain)
            msg = 'You have successfully shared %d edition(s) with %s.' % (
                len(editions), ", ".join([u.email for u in data['share_emails']]))
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete the share from our DB using datetime_deleted
        """
        data = request.data.copy()
        data['bitcoin_id'] = pk
        serializer = ShareDeleteForm(data=data, context={'request': request})
        if serializer.is_valid():
            editions = serializer.validated_data['bitcoin_id']
            for edition in editions:
                try:
                    share = Share.objects.get(new_owner=request.user, edition=edition)
                    share.delete_safe()
                except ObjectDoesNotExist:
                    pass
                share_delete.send(sender=Share, user=request.user, edition=edition, piece=edition.parent)

            msg = 'You have removed %d edition(s) from your list.' % (len(editions))

            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _share_and_email(user, editions, sharees, message, subdomain):
        for sharee in sharees:
            for edition in editions:
                s = Share.create(sharee=sharee, edition=edition, prev_owner=user)
                s.save()
            send_ascribe_email.delay(
                msg_cls=messages.ShareEditionsEmailMessage,
                to=sharee.email,
                sender=user,
                editions=editions,
                message=message,
                subdomain=subdomain,
            )

    def get_serializer_class(self):
        if self.action == "create":
            return ShareModalForm
        return OwnershipEditionSerializer


class SharePieceEndpoint(ShareEndpoint):
    queryset = SharePiece.objects.all()

    def create(self, request):

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            pieces = data['piece_id'] if isinstance(data['piece_id'], list) else [data['piece_id']]
            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key('HTTP_ORIGIN') else 'www'
            SharePieceEndpoint._share_and_email(request.user,
                                                pieces,
                                                data['share_emails'],
                                                data['share_message'],
                                                subdomain=subdomain)
            msg = 'You have successfully shared %d pieces(s) with %s.' % (
                len(pieces), ", ".join([u.email for u in data['share_emails']]))
            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete the share from our DB using datetime_deleted
        """
        data = request.data.copy()
        data['piece_id'] = pk
        serializer = SharePieceDeleteForm(data=data, context={'request': request})
        if serializer.is_valid():
            piece = serializer.validated_data['piece_id']
            try:
                share = SharePiece.objects.get(new_owner=request.user, piece=piece)
                share.delete_safe()
            except ObjectDoesNotExist:
                pass
            share_delete.send(sender=Share, user=request.user, edition=None, piece=piece)
            msg = 'You have removed piece %s by %s from your list.' % (piece.title, piece.artist_name)

            return Response({'success': True, 'notification': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _share_and_email(user, pieces, sharees, message, subdomain):
        for sharee in sharees:
            for piece in pieces:
                s = SharePiece.create(sharee=sharee, piece=piece)
                s.save()

            send_ascribe_email.delay(
                msg_cls=messages.SharePiecesEmailMessage,
                sender=user,
                to=sharee.email,
                pieces=pieces,
                message=message,
                subdomain=subdomain,
            )

    def get_serializer_class(self):
        if self.action == "create":
            return SharePieceModalForm
        return OwnershipPieceSerializer


class LicenseEndpoint(GenericViewSetKpi):
    """
    License API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = License.objects.all()
    permission_classes = [AllowAny]
    json_name = 'licenses'

    def list(self, request):
        subdomain = self.request.query_params.get('subdomain', None)
        try:
            whitelabel = WhitelabelSettings.objects.get(subdomain=subdomain)
            queryset = self.queryset.filter(organization=whitelabel.name)
        except ObjectDoesNotExist:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return LicenseSerializer

    def get_queryset(self):
        return self.queryset.filter(organization='ascribe')
