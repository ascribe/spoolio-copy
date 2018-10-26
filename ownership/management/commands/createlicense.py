# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from ownership.models import License


class Command(BaseCommand):
    help = 'Creates a license for the given whitelabel organization'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o',
            '--organization',
            required=True,
            help='whitelabel organization associated with this license',
        )
        parser.add_argument(
            '-n',
            '--license-name',
            required=True,
            help='name of the license',
        )
        parser.add_argument(
            '-c',
            '--code',
            required=True,
            help='short code for the license (e.g. "cc-by-4.0")',
        )
        parser.add_argument(
            '-u',
            '--url',
            required=True,
            help='url of the license text',
        )

    def handle(self, *args, **options):
        License.objects.create(
            name=options['license_name'],
            organization=options['organization'],
            code=options['code'],
            url=options['url'],
        )
