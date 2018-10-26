# -*- coding: utf-8 -*-

"""
Set of classed-based views for email messages. This based on DISQUS
TemplatedHTMLEmailMessageView.

Some key terminology:
    sender: the sharer, transferer, consignor, or loaner
    receiver: the sharee, transferee, consignee, or loanee

It is important not to confuse sender & receiver with the "sender of an email"
and "receiver of an email". These may differ, or may not, depending on the
email. To avoid this confusion a choice (and attempt) has been made to use the
words receiver and sender strictly for their SPOOL transaction and sharing
related usage.

"""
from __future__ import unicode_literals

from functools import wraps
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.utils.http import urlquote_plus
from django.utils.translation import ugettext as _

from mailviews.messages import TemplatedHTMLEmailMessageView
from inlinestyler.utils import inline_css

from .utils import get_signup_or_login_link
from users.models import UserNeedsToRegisterRole
from util.util import insert_or_change_subdomain


logger = logging.getLogger(__name__)


# TODO move this elsewhere, e.g.: email backend?
def is_blacklisted(recipients):
    # TODO look what kind of ways there are to know if tests are being run
    if settings.TESTING or settings.DEPLOYMENT == 'live':
        return False
    for pattern in settings.EMAIL_WHITELIST:
        for recipient in recipients:
            if recipient.lower().find(pattern) != -1:
                return False
    return True


def inlinecss(html_renderer_function):
    @wraps(html_renderer_function)
    def wrapper(*args, **kwargs):
        return inline_css(html_renderer_function(*args, **kwargs))
    return wrapper


# TODO This could perhaps be made into an abstract or meta class.
class AscribeEmailMessage(TemplatedHTMLEmailMessageView):
    """
    Base class for emails sent by ascribe for signup, password reset, shared
    works, SPOOL operations, and possibly others.

    """
    def __init__(self, to=None):
        self.to = to
        super(AscribeEmailMessage, self).__init__()

    @cached_property
    def email_safe(self):
        return urlquote_plus(self.to)

    @inlinecss
    def render_html_body(self, context):
        return super(AscribeEmailMessage, self).render_html_body(context)

    def render_to_message(self, extra_context=None, *args, **kwargs):
        assert 'to' not in kwargs  # this should only be sent to the user
        kwargs['to'] = (self.to,)
        return super(
            AscribeEmailMessage, self).render_to_message(*args, **kwargs)

    def send(self, extra_context=None, **kwargs):
        # TODO move this elsewhere, e.g.: email backend?
        if is_blacklisted((self.to,)):
            logger.warn('Email is blacklisted on non-live environments')
            return 0
        super(AscribeEmailMessage, self).send(extra_context=extra_context,
                                              **kwargs)


class OwnershipEmailMessageMixin(object):
    """
    Mixin class for emails that involve SPOOL operations.

    """
    action = None
    verb_infinitive = None
    verb_past_participle = None
    digital_work_type = None
    subject_template_name = 'emails/subject.txt'
    body_template_name = 'emails/message.txt'

    def get_button_text(self):
        return self.button_text

    # TODO bring logic from tasks within
    @cached_property
    def redirect_url(self):
        return insert_or_change_subdomain(
            settings.ASCRIBE_URL_FRONTEND, self.subdomain)

    @cached_property
    def redirect_url_safe(self):
        return urlquote_plus(self.redirect_url)

    @cached_property
    def signup_or_login_link(self):
        return get_signup_or_login_link(self.to, self.subdomain)

    # TODO figure out what the button should hyperlink to
    @property
    def safe_link(self):
        return 'not implemented'

    def get_context_data(self, **kwargs):
        context = super(
            OwnershipEmailMessageMixin, self).get_context_data(**kwargs)
        context.update({
            'subject': self.subject,
            'html_body_header': self.html_body_header,
            'sender': self.sender,
            'receiver': self.receiver,
            'editions': self.editions,
            # TODO needed for text template (|length does not work)
            'editions_qty': str(len(self.editions)),
            'message': self.message,
            'safe_link': self.safe_link,
            'signup_or_login_link': self.signup_or_login_link,
            'redirect_url': self.redirect_url,
            'redirect_url_safe': self.redirect_url_safe,
            'verb_infinitive': self.verb_infinitive,
            'verb_past_participle': self.verb_past_participle,
            'digital_work_type': self.digital_work_type,
            'button_text': self.get_button_text(),
        })
        return context


# TODO This could perhaps be made into an abstract or meta class.
class OwnershipSenderEmailMessage(OwnershipEmailMessageMixin,
                                  AscribeEmailMessage):
    """
    Base class for emails sent to a sender (e.g. transferer).

    """
    html_body_template_name = 'emails/transaction_request_sender_body.html'
    button_text = None

    def __init__(self, sender=None, receiver=None,
                 editions=None, message='', subdomain='www'):
        self.to = sender.email
        self.sender = sender
        self.receiver = receiver
        self.editions = editions
        self.message = message
        self.subdomain = subdomain
        super(OwnershipSenderEmailMessage, self).__init__(to=self.to)

    # TODO need to be implemented by subclass, or parameterized
    @cached_property
    def subject(self):
        return 'Ownership - "{}"'.format(self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} Request Sent'.format(self.action)


# TODO This could perhaps be made into an abstract or meta class.
class OwnershipReceiverEmailMessage(OwnershipEmailMessageMixin,
                                    AscribeEmailMessage):
    """
    Base class for emails sent to a receiver (e.g. transferee).

    """
    html_body_template_name = 'emails/transaction_request_receiver_body.html'

    # TODO leave to subclass, perhaps
    button_text = _('View')

    def __init__(self, sender=None, receiver=None,
                 editions=None, message='', subdomain='www'):
        self.to = receiver.email
        self.sender = sender
        self.receiver = receiver
        self.editions = editions
        self.message = message
        self.subdomain = subdomain
        super(OwnershipReceiverEmailMessage, self).__init__(to=self.to)

    def is_receiver_invited(self):
        return self.receiver.role_at_user.filter(
            type='UserNeedsToRegisterRole').exists()

    def get_button_text(self):
        if self.is_receiver_invited():
            return 'Sign Up & {}'.format(self.button_text)
        return self.button_text

    @cached_property
    def html_body_header(self):
        if len(self.editions) > 1:
            return 'Some things have been {} to you'.format(
                self.verb_past_participle)
        return 'Something has been {} to you'.format(self.verb_past_participle)

    @cached_property
    def opening_text(self):
        return None

    def get_context_data(self, **kwargs):
        context = super(
            OwnershipReceiverEmailMessage, self).get_context_data(**kwargs)
        context.update({
            'opening_text': self.opening_text,
        })
        return context


class WelcomeEmailMessage(AscribeEmailMessage):

    REDIRECT_URL = settings.ASCRIBE_URL_NO_APP + 'api/users/activate/'

    subject_template_name = 'emails/welcome/subject.txt'
    body_template_name = 'emails/welcome/body.txt'
    html_body_template_name = 'emails/welcome/body.html'

    def __init__(self, to=None, token=None, subdomain='www'):
        super(WelcomeEmailMessage, self).__init__(to=to)
        self.token = token
        self.subdomain = subdomain

    @property
    def safe_link(self):
        return '{}?token={}&email={}&subdomain={}'.format(
            self.REDIRECT_URL, self.token, self.email_safe, self.subdomain)

    def get_context_data(self, **kwargs):
        context = super(WelcomeEmailMessage, self).get_context_data(**kwargs)
        context.update({
            'safe_link': self.safe_link,
            'email_safe': self.email_safe,
            'token': self.token,
            'subdomain': self.subdomain,
            'host': self.REDIRECT_URL,
        })
        return context


class WelcomeEmailMessageCreativeCommons(WelcomeEmailMessage):

    subject_template_name = 'emails/creativecommons/subject.txt'
    html_body_template_name = 'emails/creativecommons/signup.html'


class WelcomeEmailMessage23vivi(WelcomeEmailMessage):

    subject_template_name = 'emails/23vivi/subject.txt'
    html_body_template_name = 'emails/23vivi/signup.html'


class WelcomeEmailMessageLumenus(WelcomeEmailMessage):

    subject_template_name = 'emails/lumenus/subject.txt'
    html_body_template_name = 'emails/lumenus/signup.html'

class WelcomeEmailMessageDemo(WelcomeEmailMessage):

    subject_template_name = 'emails/demo/subject.txt'
    html_body_template_name = 'emails/demo/signup.html'

class WelcomeEmailMessageLiquidGallery(WelcomeEmailMessage):

    subject_template_name = 'emails/liquidgallery/subject.txt'
    html_body_template_name = 'emails/liquidgallery/signup.html'


class WelcomeEmailMessagePolline(WelcomeEmailMessage):

    subject_template_name = 'emails/polline/subject.txt'
    html_body_template_name = 'emails/polline/signup.html'


class WelcomeEmailMessageArtcity(WelcomeEmailMessage):

    subject_template_name = 'emails/artcity/subject.txt'
    html_body_template_name = 'emails/artcity/signup.html'


class PasswordResetEmailMessage(AscribeEmailMessage):

    subject_template_name = 'emails/passwordreset/subject.txt'
    body_template_name = 'emails/passwordreset/body.txt'
    html_body_template_name = 'emails/passwordreset/body.html'

    button_text = _('Reset your password')

    def __init__(self, to=None, token=None, redirect_url=None):
        super(PasswordResetEmailMessage, self).__init__(to=to)
        self.token = token
        self.redirect_url = redirect_url

    @cached_property
    def safe_link(self):
        return '{}?token={}&email={}'.format(
            self.redirect_url, self.token, self.email_safe)

    def get_context_data(self, **kwargs):
        context = super(
            PasswordResetEmailMessage, self).get_context_data(**kwargs)
        context.update({
            'safe_link': self.safe_link,
            'button_text': self.button_text,
        })
        return context


# TODO Use mixin and/or inheritance to remove code duplication between edition
# and piece related classes
class ShareEditionsEmailMessage(AscribeEmailMessage):

    subject_template_name = 'emails/share/editions/subject.txt'
    body_template_name = 'emails/share/editions/body.txt'
    html_body_template_name = 'emails/share/editions/body.html'
    verb_past_participle = 'shared'

    button_text = _('View')

    def __init__(self, to=None, sender=None,
                 editions=None, message='', subdomain='www'):
        super(ShareEditionsEmailMessage, self).__init__(to=to)
        self.sender = sender
        self.editions = editions
        self.message = message
        self.subdomain = subdomain

    @property
    def has_receiver_signed_up(self):
        try:
            receiver = User.objects.get(email=self.to)
        except receiver.DoesNotExist:
            return False

        if UserNeedsToRegisterRole.objects.filter(
                user=receiver, type='UserNeedsToRegisterRole').exists():
            return False

        return True

    def get_button_text(self):
        if not self.has_receiver_signed_up:
            return 'Sign Up & {}'.format(self.button_text)
        return self.button_text

    @cached_property
    def html_body_header(self):
        if len(self.editions) > 1:
            return 'Some things have been {} with you'.format(
                self.verb_past_participle)
        return 'Something has been {} with you'.format(self.verb_past_participle)

    # TODO figure out what the button should hyperlink to
    @property
    def safe_link(self):
        return 'not implemented'

    # TODO for now , duplicate code, from ownership class
    @cached_property
    def signup_or_login_link(self):
        return get_signup_or_login_link(self.to, self.subdomain)

    def get_context_data(self, **kwargs):
        context = super(
            ShareEditionsEmailMessage, self).get_context_data(**kwargs)
        context.update({
            'html_body_header': self.html_body_header,
            'verb_past_participle': self.verb_past_participle,
            'sender': self.sender,
            'editions': self.editions,
            'message': self.message,
            'safe_link': self.safe_link,
            'button_text': self.get_button_text(),
            'signup_or_login_link': self.signup_or_login_link,
        })
        return context


# TODO Use mixin and/or inheritance to remove code duplication between edition
# and piece related classes
class SharePiecesEmailMessage(AscribeEmailMessage):

    subject_template_name = 'emails/share/pieces/subject.txt'
    body_template_name = 'emails/share/pieces/body.txt'
    html_body_template_name = 'emails/share/pieces/body.html'
    verb_past_participle = 'shared'

    button_text = _('View')

    def __init__(self, to=None, sender=None,
                 pieces=None, message='', subdomain='www'):
        super(SharePiecesEmailMessage, self).__init__(to=to)
        self.sender = sender
        self.pieces = pieces
        self.message = message
        self.subdomain = subdomain

    @property
    def has_receiver_signed_up(self):
        try:
            receiver = User.objects.get(email=self.to)
        except receiver.DoesNotExist:
            return False

        if UserNeedsToRegisterRole.objects.filter(
                user=receiver, type='UserNeedsToRegisterRole').exists():
            return False

        return True

    def get_button_text(self):
        if not self.has_receiver_signed_up:
            return 'Sign Up & {}'.format(self.button_text)
        return self.button_text

    @cached_property
    def html_body_header(self):
        if len(self.pieces) > 1:
            return 'Some things have been {} with you'.format(
                self.verb_past_participle)
        return 'Something has been {} with you'.format(self.verb_past_participle)

    # TODO figure out what the button should hyperlink to
    @property
    def safe_link(self):
        return 'not implemented'

    @cached_property
    def signup_or_login_link(self):
        return get_signup_or_login_link(self.to, self.subdomain)

    def get_context_data(self, **kwargs):
        context = super(
            SharePiecesEmailMessage, self).get_context_data(**kwargs)
        context.update({
            'html_body_header': self.html_body_header,
            'verb_past_participle': self.verb_past_participle,
            'sender': self.sender,
            'pieces': self.pieces,
            'message': self.message,
            'safe_link': self.safe_link,
            'button_text': self.get_button_text(),
            'signup_or_login_link': self.signup_or_login_link,
        })
        return context


class TransferEmailMessage(OwnershipReceiverEmailMessage):

    action = 'Transfer'
    verb_infinitive = 'transfer'
    verb_past_participle = 'transferred'

    @cached_property
    def subject(self):
        return 'Transferred to you - "{}"'.format(self.editions[0].title)

    @cached_property
    def opening_text(self):
        return '{} has {} you'.format(self.sender.username,
                                      self.verb_past_participle)


class TransferEmailMessageWhitelabelMarket(TransferEmailMessage):
    """
    Overrides `self.subdomain`'s value to www,
    instead of the whitelabels subdomain.
    """

    @cached_property
    def redirect_url(self):
        """
        For "whitelabel markets", we want to redirect a receiver of a transfer
        email (read: a buyer) to ascribe's main wallet instead of the consignment
        wallet.
        """
        return insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND, 'www')


class TransferEmailMessage23vivi(TransferEmailMessageWhitelabelMarket):

    html_body_template_name = 'emails/23vivi/transaction_request_receiver_body.html'


class TransferEmailMessageLumenus(TransferEmailMessageWhitelabelMarket):

    html_body_template_name = 'emails/lumenus/transaction_request_receiver_body.html'


class TransferEmailMessagePolline(TransferEmailMessage):

    html_body_template_name = 'emails/polline/transaction_request_receiver_body.html'


class TransferEmailMessageArtcity(TransferEmailMessage):

    html_body_template_name = 'emails/artcity/transaction_request_receiver_body.html'


class TransferEmailMessageDemo(TransferEmailMessage):

    html_body_template_name = 'emails/demo/transaction_request_receiver_body.html'


class TransferEmailMessageLiquidGallery(TransferEmailMessage):

    html_body_template_name = 'emails/liquidgallery/transaction_request_receiver_body.html'


class ConsignRequestReceiverEmailMessage(OwnershipReceiverEmailMessage):

    action = 'Consignment'
    verb_infinitive = 'consign'
    verb_past_participle = 'consigned'
    button_text = _('Review')

    @cached_property
    def subject(self):
        return '{} Request Pending - "{}"'.format(self.action,
                                                  self.editions[0].title)


class LoanRequestReceiverEmailMessage(OwnershipReceiverEmailMessage):

    action = 'Loan'
    verb_infinitive = 'loan'
    verb_past_participle = 'loaned'
    button_text = _('Review')

    @cached_property
    def subject(self):
        return '{} Request Pending - "{}"'.format(self.action,
                                                  self.editions[0].title)


class UnconsignmentRequestReceiverEmailMessage(OwnershipReceiverEmailMessage):

    action = 'Unconsignment'
    verb_infinitive = 'unconsign'
    verb_past_participle = 'unconsigned'
    button_text = _('Review')

    @cached_property
    def subject(self):
        return '{} Request - "{}"'.format(self.action, self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} Request'.format(self.action)

    @cached_property
    def opening_text(self):
        return '{} has requested you to {}'.format(self.sender.username,
                                                   self.verb_infinitive)


class ConsignRequestSenderEmailMessage(OwnershipSenderEmailMessage):

    action = 'Consignment'
    verb_past_participle = 'consigned'
    body_template_name = 'emails/consign/request/sender/body.txt'

    @cached_property
    def subject(self):
        return '{} Request Sent - "{}"'.format(self.action,
                                               self.editions[0].title)


class ConsignRequestSenderEmailMessage23vivi(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/23vivi/owner_onrequest_consign.html'


class ConsignRequestSenderEmailMessageLumenus(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/lumenus/owner_onrequest_consign.html'


class ConsignRequestSenderEmailMessagePolline(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/polline/owner_onrequest_consign.html'


class ConsignRequestSenderEmailMessageArtcity(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/artcity/owner_onrequest_consign.html'


class ConsignRequestSenderEmailMessageDemo(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/demo/owner_onrequest_consign.html'


class ConsignRequestSenderEmailMessageLiquidGallery(ConsignRequestSenderEmailMessage):

    html_body_template_name = 'emails/liquidgallery/owner_onrequest_consign.html'


class LoanRequestSenderEmailMessage(OwnershipSenderEmailMessage):

    action = 'Loan'
    digital_work_type = 'edition'
    verb_past_participle = 'loaned'
    body_template_name = 'emails/loan/request/sender_body.txt'

    @cached_property
    def subject(self):
        return '{} Request Sent - "{}"'.format(self.action,
                                               self.editions[0].title)


class LoanPieceRequestSenderEmailMessage(OwnershipSenderEmailMessage):

    action = 'Loan'
    digital_work_type = 'piece'
    html_body_template_name = 'emails/loan/request_loan_pieces_to_loaner.html'
    button_text = _('Review')

    @cached_property
    def subject(self):
        return '{} Request - "{}"'.format(self.action, self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} Request'.format(self.action)


class LoanPieceRequestReceiverEmailMessage(OwnershipReceiverEmailMessage):

    action = 'Loan'
    digital_work_type = 'piece'
    body_template_name = 'emails/transaction_request_by_receiver.txt'
    html_body_template_name = 'emails/transaction_piece_request_receiver_body.html'

    @cached_property
    def subject(self):
        return '{} Request Sent - "{}"'.format(
            self.action, self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} Request Sent'.format(self.action)


class TransactionStateChangeMixin(object):
    """
    Mixin class for emails that involve a state change of a transaction, such
    as transitioning from "pending" to "accepted".

    """
    @cached_property
    def subject(self):
        return '{} {} - "{}"'.format(
            self.action, self.state, self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} {}'.format(self.action, self.state)


class ConsignConfirmSenderEmailMessage(TransactionStateChangeMixin,
                                       OwnershipSenderEmailMessage):

    action = 'Consignment'
    state = 'Accepted'
    body_template_name = 'emails/consign/confirm/sender/body.txt'
    html_body_template_name = 'emails/transaction_accepted_sender_body.html'


class ConsignConfirmSenderEmailMessage23vivi(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/23vivi/owner_onconfirmconsign.html'


class ConsignConfirmSenderEmailMessageLumenus(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/lumenus/owner_onconfirmconsign.html'


class ConsignConfirmSenderEmailMessagePolline(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/polline/owner_onconfirmconsign.html'


class ConsignConfirmSenderEmailMessageArtcity(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/artcity/owner_onconfirmconsign.html'


class ConsignConfirmSenderEmailMessageDemo(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/demo/owner_onconfirmconsign.html'


class ConsignConfirmSenderEmailMessageLiquidGallery(ConsignConfirmSenderEmailMessage):

    html_body_template_name = 'emails/liquidgallery/owner_onconfirmconsign.html'


class LoanConfirmSenderEmailMessage(TransactionStateChangeMixin,
                                    OwnershipSenderEmailMessage):

    action = 'Loan'
    state = 'Accepted'
    body_template_name = 'emails/loan/confirm/sender_body.txt'
    html_body_template_name = 'emails/transaction_accepted_sender_body.html'


class LoanPieceConfirmReceiverEmailMessage(TransactionStateChangeMixin,
                                           OwnershipReceiverEmailMessage):

    action = 'Loan'
    state = 'Accepted'
    verb_infinitive = 'loan'
    body_template_name = 'emails/transaction_confirmed_by_sender.txt'
    html_body_template_name = 'emails/transaction_piece_accepted_receiver_body.html'


class LoanPieceDenyReceiverEmailMessage(TransactionStateChangeMixin,
                                        OwnershipReceiverEmailMessage):

    action = 'Loan'
    state = 'Rejected'
    verb_infinitive = 'loan'
    body_template_name = 'emails/transaction_denied_by_sender.txt'
    html_body_template_name = 'emails/transaction_piece_rejected_receiver_body.html'


class ConsignDenySenderEmailMessage(TransactionStateChangeMixin,
                                    OwnershipSenderEmailMessage):

    action = 'Consignment'
    state = 'Rejected'
    body_template_name = 'emails/consign/deny/sender/body.txt'
    html_body_template_name = 'emails/transaction_rejected_sender_body.html'
    button_text = _('View')


class ConsignDenySenderEmailMessage23vivi(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/23vivi/owner_ondenyconsign.html'


class ConsignDenySenderEmailMessageLumenus(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/lumenus/owner_ondenyconsign.html'


class ConsignDenySenderEmailMessagePolline(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/polline/owner_ondenyconsign.html'


class ConsignDenySenderEmailMessageArtcity(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/artcity/owner_ondenyconsign.html'


class ConsignDenySenderEmailMessageDemo(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/demo/owner_ondenyconsign.html'


class ConsignDenySenderEmailMessageLiquidGallery(ConsignDenySenderEmailMessage):

    html_body_template_name = 'emails/liquidgallery/owner_ondenyconsign.html'


class LoanDenySenderEmailMessage(TransactionStateChangeMixin,
                                 OwnershipSenderEmailMessage):

    action = 'Loan'
    state = 'Rejected'
    body_template_name = 'emails/loan/deny/sender_body.txt'
    html_body_template_name = 'emails/transaction_rejected_sender_body.html'
    button_text = _('View')


class UnconsignmentDenySenderEmailMessage(TransactionStateChangeMixin,
                                          OwnershipSenderEmailMessage):

    action = 'Unconsignment'
    state = 'Rejected'
    body_template_name = 'emails/consign/terminate/denied_sender_body.txt'
    html_body_template_name = 'emails/transaction_rejected_sender_body.html'
    button_text = _('View')


class ConsignTerminateSenderEmailMessage(OwnershipSenderEmailMessage):

    action = 'Unconsignment'
    verb_infinitive = 'unconsign'
    verb_past_participle = 'unconsigned'
    html_body_template_name = 'emails/transaction_notification_sender_body.html'

    @cached_property
    def subject(self):
        return '{} Notification - "{}"'.format(self.action,
                                               self.editions[0].title)

    @cached_property
    def html_body_header(self):
        return '{} Notification'.format(self.action)
