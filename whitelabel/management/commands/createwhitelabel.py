# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from whitelabel.models import WhitelabelSettings


ACLS = (
    'acl_unconsign',
    'acl_edit',
    'acl_request_unconsign',
    'acl_create_editions',
    'acl_wallet_submitted',
    'acl_coa',
    'acl_download',
    'acl_share',
    'acl_edit_public_contract',
    'acl_transfer',
    'acl_view_settings_api',
    'acl_withdraw_consign',
    'acl_view_powered_by',
    'acl_wallet_accepted',
    'acl_view',
    'acl_wallet_submit',
    'acl_withdraw_transfer',
    'acl_view_settings_bitcoin',
    'acl_view_settings_account_hash',
    'acl_consign',
)

WHITELABEL_S3_PATH = 'https://{host}/{bucket}/whitelabel/'.format(
    host=settings.AWS_S3_HOST,
    bucket=settings.AWS_STORAGE_BUCKET_NAME,
)

HEAD = {
    'meta': {
        'ms3': {
            'content': '#ffffff',
            'name': 'theme-color'
        },
        'ms2': {
            'content': WHITELABEL_S3_PATH + '{subdomain}/mstile-144x144.png',
            'name': 'msapplication-TileImage'
        },
        'ms1': {
            'content': '#da532c',
            'name': 'msapplication-TileColor'
        }
    },
    'link': {
        'icon4': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/android-chrome-192x192.png',
            'type': 'image/png',
            'rel': 'icon',
            'sizes': '192x192'
        },
        'icon1': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/favicon-32x32.png',
            'type': 'image/png',
            'rel': 'icon',
            'sizes': '32x32'
        },
        'icon2': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/favicon-96x96.png',
            'type': 'image/png',
            'rel': 'icon',
            'sizes': '96x96'
        },
        'icon3': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/favicon-16x16.png',
            'type': 'image/png',
            'rel': 'icon',
            'sizes': '16x16'
        },
        'manifest': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/manifest.json',
            'rel': 'manifest'
        },
        'apple6': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-120x120.png',
            'rel': 'apple-touch-icon',
            'sizes': '120x120'
        },
        'apple7': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-144x144.png',
            'rel': 'apple-touch-icon',
            'sizes': '144x144'
        },
        'apple4': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-76x76.png',
            'rel': 'apple-touch-icon',
            'sizes': '76x76'
        },
        'apple5': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-114x114.png',
            'rel': 'apple-touch-icon',
            'sizes': '114x114'
        },
        'apple2': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-60x60.png',
            'rel': 'apple-touch-icon',
            'sizes': '60x60'
        },
        'apple3': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-72x72.png',
            'rel': 'apple-touch-icon',
            'sizes': '72x72'
        },
        'apple1': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-57x57.png',
            'rel': 'apple-touch-icon',
            'sizes': '57x57'
        },
        'apple8': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-152x152.png',
            'rel': 'apple-touch-icon',
            'sizes': '152x152'
        },
        'apple9': {
            'href': WHITELABEL_S3_PATH + '{subdomain}/apple-touch-icon-180x180.png',
            'rel': 'apple-touch-icon',
            'sizes': '180x180'
        }
    }
}


class Command(BaseCommand):
    help = 'Creates a whitelabel for the given admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--user-email',
            # TODO
            # required=True,
            help='email of the user managing the whitelabel',
        )
        parser.add_argument(
            '-s',
            '--subdomain',
            # TODO
            # required=True,
            help='subdomain',
        )
        parser.add_argument(
            '-n',
            '--whitelabel-name',
            # TODO
            # required=True,
            help='name of whitelabel',
        )
        parser.add_argument('-l', '--logo')
        parser.add_argument('--acl-unconsign', default=True)
        parser.add_argument('--acl-edit', default=True)
        parser.add_argument('--acl-request-unconsign', default=True)
        parser.add_argument('--acl-create-editions', default=True)
        parser.add_argument('--acl-wallet-submitted', default=True)
        parser.add_argument('--acl-coa', default=True)
        parser.add_argument('--acl-download', default=True)
        parser.add_argument('--acl-share', default=True)
        parser.add_argument('--acl-edit-public-contract', default=True)
        parser.add_argument('--acl-transfer', default=True)
        parser.add_argument('--acl-view-settings-api', default=False)
        parser.add_argument('--acl-withdraw-consign', default=True)
        parser.add_argument('--acl-view-powered-by', default=True)
        parser.add_argument('--acl-wallet-accepted', default=True)
        parser.add_argument('--acl-view', default=True)
        parser.add_argument('--acl-wallet-submit', default=True)
        parser.add_argument('--acl-withdraw-transfer', default=True)
        parser.add_argument('--acl-view-settings-bitcoin', default=False)
        parser.add_argument('--acl-view-settings-account-hash', default=False)
        parser.add_argument('--acl-consign', default=True)

    def handle(self, *args, **options):
        User = get_user_model()
        # TODO use required=True when adding the argument instead of checking
        # for it -- the problem is to then test it
        try:
            email = options['user_email']
        except KeyError:
            raise CommandError('user-email is required')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError('User "{}" does not exist'.format(email))

        # TODO use required=True when adding the argument instead of checking
        # for it -- the problem is to then test it
        try:
            subdomain = options['subdomain']
        except KeyError:
            raise CommandError('subdomain is required')

        # TODO use required=True when adding the argument instead of checking
        # for it -- the problem is to then test it
        try:
            name = options['whitelabel_name']
        except KeyError:
            raise CommandError('whitelabel-name is required')

        logo = options.get('logo')
        acls = {acl: options[acl] for acl in ACLS}

        HEAD['meta']['ms2']['content'] = HEAD['meta']['ms2']['content'].format(subdomain=subdomain)

        for k in HEAD['link']:
            HEAD['link'][k]['href'] = HEAD['link'][k]['href'].format(subdomain=subdomain)

        WhitelabelSettings.objects.create(
            user=user, subdomain=subdomain, name=name, title=name, head=HEAD, logo=logo, **acls)
