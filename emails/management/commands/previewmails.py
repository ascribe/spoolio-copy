import functools
import os

from django.core.management.base import CommandError
from django.contrib.auth.models import User

from core.management.base import PatchedBaseCommand
from emails import messages, tasks
from emails.tasks import send_ascribe_email
from piece.models import Edition, Piece
from users.models import UserNeedsToRegisterRole


def send_ownership_mail_handler(options, func=None, msg_cls=None):
    sender_email = options['sender']
    receiver_email = options['receiver']
    message = options['message']
    subdomain = options['subdomain']
    sender = User.objects.get(email=sender_email)
    language = options['language']
    # TODO workaround to deal with cases involving pieces, instead of editions
    if msg_cls in (
        messages.LoanPieceRequestSenderEmailMessage,
        messages.LoanPieceRequestReceiverEmailMessage,
        messages.LoanPieceConfirmReceiverEmailMessage,
        messages.LoanPieceDenyReceiverEmailMessage,
    ):
        digiwork_obj_qs = Piece.objects.filter(pk__in=options['pieces'])
    else:
        digiwork_obj_qs = Edition.objects.filter(pk__in=options['editions'])

    try:
        receiver = User.objects.get(email=receiver_email)
    except User.DoesNotExist:
        # NOTE this is only meant to be used for testing purposes
        receiver = User.objects.create(
            email=receiver_email,
            username=receiver_email.split('@')[0][:30],
        )
        UserNeedsToRegisterRole.objects.create(user=receiver,
                                               type='UserNeedsToRegisterRole')
    if func:
        getattr(tasks, func)(
            sender=sender,
            receiver=receiver,
            editions=digiwork_obj_qs,
            message=message,
            subdomain=subdomain,
        )
    elif msg_cls:
        send_ascribe_email(
            msg_cls=msg_cls,
            sender=sender,
            receiver=receiver,
            editions=digiwork_obj_qs,
            message=message,
            subdomain=subdomain,
            lang=language,
        )


def welcome(options):
    to = options['to']
    subdomain = options['subdomain']
    language = options['language']
    if subdomain == 'cc':
        msg_cls = messages.WelcomeEmailMessageCreativeCommons
    elif subdomain == '23vivi':
        msg_cls = messages.WelcomeEmailMessage23vivi
    else:
        msg_cls = messages.WelcomeEmailMessage
    send_ascribe_email(
        msg_cls=msg_cls,
        to=to,
        token='token',
        subdomain=subdomain,
        lang=language,
    )


def password_reset(options):
    to = options['to']
    language = options['language']
    send_ascribe_email(
        msg_cls=messages.PasswordResetEmailMessage,
        to=to,
        token='token',
        redirect_url='redirecturl',
        lang=language,
    )


def share_pieces(options):
    to = options['receiver']
    sender_email = options['sender']
    pieces = options['pieces']
    message = options['message']
    subdomain = options['subdomain']
    piece_obj_qs = Piece.objects.filter(pk__in=pieces)
    sender = User.objects.get(email=sender_email)
    send_ascribe_email(
        msg_cls=messages.SharePiecesEmailMessage,
        sender=sender,
        to=to,
        pieces=piece_obj_qs,
        message=message,
        subdomain=subdomain,
        lang='en',
    )


def share_editions(options):
    to = options['receiver']
    sender_email = options['sender']
    editions = options['editions']
    message = options['message']
    subdomain = options['subdomain']
    edition_obj_qs = Edition.objects.filter(pk__in=editions)
    sender = User.objects.get(email=sender_email)
    messages.ShareEditionsEmailMessage(
        to=to,
        sender=sender,
        editions=edition_obj_qs,
        message=message,
        subdomain=subdomain,
    ).send()

transferee = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.TransferEmailMessage,
)

consignee_request = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.ConsignRequestReceiverEmailMessage,
)

consignor_request = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.ConsignRequestSenderEmailMessage,
)

consignor_confirm = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.ConsignConfirmSenderEmailMessage,
)

consignor_deny = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.ConsignDenySenderEmailMessage,
)

consignee_terminate_request = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.UnconsignmentRequestReceiverEmailMessage,
)

loanee = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanRequestReceiverEmailMessage,
)

loaner = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanRequestSenderEmailMessage,
)

loaner_confirm = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanConfirmSenderEmailMessage,
)

loaner_deny = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanDenySenderEmailMessage,
)

loaner_piece = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanPieceRequestSenderEmailMessage,
)

loanee_piece = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanPieceRequestReceiverEmailMessage,
)

loanee_piece_confirm = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanPieceConfirmReceiverEmailMessage,
)

loanee_piece_deny = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.LoanPieceDenyReceiverEmailMessage,
)

consignor_terminate = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.ConsignTerminateSenderEmailMessage,
)

consignor_terminate_deny = functools.partial(
    send_ownership_mail_handler,
    msg_cls=messages.UnconsignmentDenySenderEmailMessage,
)


def all_emails(options):
    del ACTION_MAP['all']
    if options['without_loan_piece']:
        del ACTION_MAP['loaner-piece']
        del ACTION_MAP['loanee-piece']
        del ACTION_MAP['loanee-piece-confirm']
        del ACTION_MAP['loanee-piece-deny']

    count = 0
    for action, attrs in ACTION_MAP.items():
        try:
            func = attrs['func']
        except KeyError:
            pass
        else:
            func(options)
            count += 1
    return count

ACTION_MAP = {
    'welcome': {
        'help': 'welcome email',
        'func': welcome,
        'arg_meta_list': [
            {'args': ('-t', '--to'),
             'kwargs': dict(type=str, help='recipient email')},
        ],
    },
    'password': {
        'help': 'send password reset email',
        'func': password_reset,
        'arg_meta_list': [
            {'args': ('-t', '--to'),
             'kwargs': dict(type=str, help='recipient email')},
        ],
    },
}

OWNERSHIP_ACTION_MAP = {
    'all': {
        'help': 'sends all ownership related emails',
        'func': all_emails,
        'arg_meta_list': [
            {'args': ('-t', '--to'),
             'kwargs': dict(type=str, help='recipient email')},
            {'args': ('-p', '--pieces'),
             'kwargs': dict(type=int, nargs='*', help='piece id(s)')},
            {'args': ('-e', '--editions'),
             'kwargs': dict(type=int, nargs='*', help='edition id(s)')},
            {'args': ('--without-loan-piece',),
             'kwargs': dict(action='store_true',
                            help='exclude loan piece cases')},
        ],
    },
}

PIECE_BASED_ACTION_MAP = {
    'share-pieces': {
        'help': 'share pieces action email',
        'func': share_pieces,
    },
    'loaner-piece': {
        'help': 'send loan piece request to loaner',
        'func': loaner_piece,
    },
    'loanee-piece': {
        'help': 'send loan piece request to loanee',
        'func': loanee_piece,
    },
    'loanee-piece-confirm': {
        'help': 'send loan request to loanee',
        'func': loanee_piece_confirm,
    },
    'loanee-piece-deny': {
        'help': 'send loan request to loanee',
        'func': loanee_piece_deny,
    },
}

EDITION_BASED_ACTION_MAP = {
    'share-editions': {
        'help': 'share editions action email',
        'func': share_editions,
    },
    'transferee': {
        'help': 'transfer editions action email',
        'func': transferee,
    },
    'consignee-request': {
        'help': 'send consign request email to consignee',
        'func': consignee_request,
    },
    'consignor-request': {
        'help': 'send consign request email to consignor',
        'func': consignor_request,
    },
    'consignor-confirm': {
        'help': 'send consign confirmation email to consignor',
        'func': consignor_confirm,
    },
    'consignee-confirm': {
        'help': 'send consign confirmation email to consignee',
    },
    'consignor-deny': {
        'help': 'send consign denial email to consignor',
        'func': consignor_deny,
    },
    'consignee-deny': {
        'help': 'send consign denial email to consignee',
    },
    'consignor-terminate': {
        'help': 'send consign termination email to consignor',
        'func': consignor_terminate,
    },
    'consignor-terminate-deny': {
        'help': 'send consign termination denial email to consignor',
        'func': consignor_terminate_deny,
    },
    'consignee-terminate-request': {
        'help': 'send consign termination email to consignor',
        'func': consignee_terminate_request,
    },
    'loanee': {
        'help': 'send loan request to loanee',
        'func': loanee,
    },
    'loaner': {
        'help': 'send loan request to loanee',
        'func': loaner,
    },
    'loaner-confirm': {
        'help': 'send loan request to loanee',
        'func': loaner_confirm,
    },
    'loaner-deny': {
        'help': 'send loan request to loanee',
        'func': loaner_deny,
    },
}

for action in PIECE_BASED_ACTION_MAP:
    PIECE_BASED_ACTION_MAP[action]['arg_meta_list'] = [
        {'args': ('-p', '--pieces'),
         'kwargs': dict(type=int, nargs='*', help='piece id(s)')},
    ]

for action in EDITION_BASED_ACTION_MAP:
    EDITION_BASED_ACTION_MAP[action]['arg_meta_list'] = [
        {'args': ('-e', '--editions'),
         'kwargs': dict(type=int, nargs='*', help='edition id(s)')},
    ]

OWNERSHIP_ACTION_MAP.update(PIECE_BASED_ACTION_MAP)
OWNERSHIP_ACTION_MAP.update(EDITION_BASED_ACTION_MAP)

for action in OWNERSHIP_ACTION_MAP:
    OWNERSHIP_ACTION_MAP[action]['arg_meta_list'].extend(
        ({'args': ('-s', '--sender'),
          'kwargs': {'type': str, 'help': 'sender email'}},
         {'args': ('-r', '--receiver'),
          'kwargs': dict(type=str, help='receiver email')},
         {'args': ('-m', '--message'),
          'kwargs': dict(type=str, default='')})
    )

ACTION_MAP.update(OWNERSHIP_ACTION_MAP)

for action in ACTION_MAP:
    ACTION_MAP[action]['arg_meta_list'].extend(
        ({'args': ('-f', '--from_email'),
          'kwargs': dict(type=str, help='from email')},
         {'args': ('--subdomain',),
          'kwargs': dict(type=str, default='www')},
         {'args': ('-l', '--language'),
          'kwargs': dict(type=str, choices=('en', 'fr'),
                         help='language in which the email should be')})
    )


class Command(PatchedBaseCommand):
    help = 'Sends emails for preview purposes'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subparser',
                                           help='sub-command help')

        for action, attrs in ACTION_MAP.items():
            parser = subparsers.add_parser(action, help=attrs['help'])
            for arg_meta in attrs['arg_meta_list']:
                parser.add_argument(*arg_meta['args'], **arg_meta['kwargs'])

    def handle(self, *args, **options):
        if os.environ['DEPLOYMENT'] != 'local':
            raise CommandError('Only for dev (local) environment')

        subparser = options['subparser']

        return_value = ACTION_MAP[subparser]['func'](options)
        self.stdout.write(79*'-')
        self.stdout.write('\n\n')
        self.stdout.write('* command: {}'.format(subparser))
        if subparser == 'all':
            self.stdout.write('* email count: {}'.format(return_value))
