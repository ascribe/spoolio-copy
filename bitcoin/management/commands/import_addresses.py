"""
Import addresses to bitcoind so that we can get the unspents
No need to check for duplicate addresses. bitcoind does not complain if
we try to add an address that already exists.
After importing all the addresses we should rescan the blockain use the rescan
command.
"""

from django.core.management.base import NoArgsCommand
from bitcoin.tasks import import_addresses


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        import_addresses.delay()
