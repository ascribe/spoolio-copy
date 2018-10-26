"""
Refill ascribe main wallet with tokens (600 satoshi) and fees (10000 satoshi)
Re-initialize federation wallet after finish
"""

from django.core.management.base import BaseCommand
from celery import chain

from bitcoin.tasks import refill_main_wallet, SpoolAction
from util.celery import app


@app.task(base=SpoolAction, bind=True, max_retries=None)
def monitor_refill(self, txid):
    conf = monitor_refill.transactions.get(txid).get('confirmations', 0)
    if not conf:
        self.retry(countdown=120)


@app.task
def initilialize_federation_db():
    # initialize_federation_wallet()
    pass


@app.task
def refill(fees, tokens):
    res = chain([refill_main_wallet.si(fees=fees, tokens=tokens), monitor_refill.s(), initilialize_federation_db.si()])
    res()
    print 'Finished refilling federation wallet'


class Command(BaseCommand):
    help = """
    Refill main wallet with fees and tokens

    usage:
        python manage.py refill <#fees> <#tokens>

    example:
        python manage.py refill 10 20
    """

    def add_arguments(self, parser):
        parser.add_argument('fees', help="number of fees (10k satoshi)", type=int)
        parser.add_argument('tokens', help="number of tokens (600 satoshi)", type=int)

    def handle(self, *args, **options):
        refill(options['fees'], options['tokens'])
