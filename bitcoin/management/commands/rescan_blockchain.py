"""
Force rescan of the blockchain without needing to restart bitcoind.
We do this by adding the mainaddress and adding the rescan Flag as true.
"""

from django.core.management.base import NoArgsCommand
from transactions import Transactions

from bitcoin.models import BitcoinWallet
from django.conf import settings
from util.celery import app


@app.task
def rescan():
    print 'Rescanning the blockchain. This may take several minutes...'
    transactions = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET,
                                username=settings.BTC_USERNAME, password=settings.BTC_PASSWORD,
                                host=settings.BTC_HOST, port=settings.BTC_PORT)
    main_address = BitcoinWallet.mainAdminBtcAddress()
    print 'Sending rescan command to {} main address {}'.format(settings.BTC_HOST, main_address)
    transactions.import_address(main_address, 'mainaddress', rescan=True)


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        rescan.delay()
