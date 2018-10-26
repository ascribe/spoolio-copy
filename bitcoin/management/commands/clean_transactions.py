from django.core.management.base import NoArgsCommand
from django.db.models import Q
from bitcoin.models import BitcoinTransaction
from ownership.models import Ownership
from util.celery import app

from transactions import Transactions


@app.task
def check_unconfirmed_transactions():
    # Check for unconfirmed transactions and set status to 2 if confirmed

    transactions = Transactions()
    count = 0
    for t in BitcoinTransaction.objects.filter(Q(status=0) | Q(status=1), tx__isnull=False):
        try:
            conf = transactions.get(t.tx).get('confirmations', 0)
        except Exception as e:
            conf = 0

        if conf > 0:
            t.status = 2
            t.save()
            count += 1
    print "Set status of {} transactions to 2".format(count)


@app.task
def clean_ciphertext_password():
    # Check for ownership entries with ciphertext_password set and with transactions already confirmed and
    # set password to None
    count = 0
    for o in Ownership.objects.filter(btc_tx__status=2, ciphertext_password__isnull=False):
        o.ciphertext_password = None
        o.save()
        count += 1
    print 'Cleared {} ciphertext_passwords'.format(count)


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        check_unconfirmed_transactions.delay()
        clean_ciphertext_password.delay()
