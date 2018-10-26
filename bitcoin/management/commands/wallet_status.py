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
def wallet_status():
    print 'Checking Federation wallet status...'
    transactions = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET,
                                username=settings.BTC_USERNAME, password=settings.BTC_PASSWORD,
                                host=settings.BTC_HOST, port=settings.BTC_PORT)
    main_address = BitcoinWallet.mainAdminBtcAddress()
    unspents = transactions.get(main_address, min_confirmations=1)['unspents']
    fees = 0
    tokens = 0
    for u in unspents:
        if u['amount'] == settings.BTC_TOKEN:
            tokens += 1
        elif u['amount'] == settings.BTC_FEE:
            fees += 1

    print "Wallet {} has {} tokens and {} fees".format(main_address, tokens, fees)


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        wallet_status.delay()
