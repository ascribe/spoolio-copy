import re
import logging

import blocktrail

from transactions import Transactions

from datetime import timedelta

from django.db import connection
from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.utils import timezone

from celery import Task, chain
from celery.task import periodic_task
from random import randint
from spool import Spool
from spool.spool import SpoolFundsError

from bitcoin.models import BitcoinTransaction, BitcoinWallet, FederationWallet
from bitcoin.models import TX_UNCONFIRMED, TX_CONFIRMED, TX_PENDING, TX_REJECTED
from ownership.models import Ownership
from piece.models import Piece, Edition
from util.celery import app
from util import crypto
from util.util import warn_ascribe_devel
from util import util

logger = logging.getLogger(__name__)


TIMEOUT = 60

# Select and delete the unspents with a locked table
query_sql_main = """
LOCK TABLE bitcoin_federationwallet IN ACCESS EXCLUSIVE MODE;
DELETE FROM bitcoin_federationwallet
WHERE (id, amount, vout, txid) IN ((
SELECT id, amount, vout, txid FROM bitcoin_federationwallet WHERE amount={} LIMIT %d)
UNION (SELECT id, amount, vout, txid FROM bitcoin_federationwallet WHERE amount={} LIMIT %d))
RETURNING id, amount, vout, txid
""".format(settings.BTC_TOKEN, settings.BTC_FEE)

query_sql_refill = """
LOCK TABLE bitcoin_federationwallet IN ACCESS EXCLUSIVE MODE;
DELETE FROM bitcoin_federationwallet
WHERE (id, amount, vout, txid) IN (
SELECT id, amount, vout, txid FROM bitcoin_federationwallet WHERE amount={} LIMIT 1)
RETURNING id, amount, vout, txid
""".format(settings.BTC_CHUNK)


class BackendSpool(Spool):
    # Spool with custom input selection to prevent double spents

    def select_inputs(self, address, nfees, ntokens, min_confirmations=6):
        # select inputs from the federation wallet
        if address == BitcoinWallet.mainAdminBtcAddress():
            cursor = connection.cursor()
            cursor.execute(query_sql_main % (ntokens, nfees))
            desc = cursor.description
            unspents = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
            fees = filter(lambda d: d['amount'] == settings.BTC_FEE, unspents)
            tokens = filter(lambda d: d['amount'] == settings.BTC_TOKEN, unspents)
            if len(fees) != nfees or len(tokens) != ntokens:
                raise SpoolFundsError('Not enough unspents for transaction')

            return fees + tokens
        else:
            # select inputs from the user HD wallet
            return super(BackendSpool, self).select_inputs(address, nfees, ntokens, min_confirmations=1)


class SpoolAction(Task):
    abstract = True
    spool = None
    transactions = None

    # initialize if BTC is enabled
    if settings.BTC_ENABLED:
        logger.info('Using service: {}'.format(settings.BTC_SERVICE))
        spool = BackendSpool(service=settings.BTC_SERVICE, username=settings.BTC_USERNAME,
                             password=settings.BTC_PASSWORD,
                             host=settings.BTC_HOST, port=settings.BTC_PORT,
                             testnet=settings.BTC_TESTNET,
                             fee=settings.BTC_FEE, token=settings.BTC_TOKEN)
        transactions = spool._t

        # blocktrail client
        blocktrail_client = blocktrail.APIClient(api_key=settings.BLOCKTRAIL_API_KEY,
                                                 api_secret=settings.BLOCKTRAIL_API_SECRET,
                                                 testnet=settings.BTC_TESTNET)

    def __call__(self, *args, **kwargs):
        # we will catch exceptions here, analyse them and decide what to do later
        try:
            # call only if btc is enabled
            if settings.BTC_ENABLED:
                return super(SpoolAction, self).__call__(*args, **kwargs)
            else:
                logger.info('BTC_ENABLED is False. Skipping: {}'.format(self.name))

        except Exception as e:
            # TODO: Log exception
            print e
            if super(SpoolAction, self).__name__ not in ['monitor', 'do_transaction', 'monitor_refill',
                                                         'transaction_monitor', 'initialize']:
                countdown = randint(100, 120)
                logger.info('retrying task {} in {}s'.format(super(SpoolAction, self).__name__, countdown))
                self.retry(exc=e, countdown=countdown, max_retries=5)
            else:
                raise

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        analyser.apply_async((exc, task_id, args, kwargs, einfo))

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        pass

    def on_success(self, retval, task_id, args, kwargs):
        # call subscribe to blocktrail event
        if settings.BTC_ENABLED and self.name not in ['bitcoin.tasks.transaction_monitor',
                                                      'bitcoin.tasks.check_status',
                                                      'bitcoin.tasks.refill_main_wallet',
                                                      'bitcoin.tasks.initialize',
                                                      'bitcoin.tasks.initialize_federation_wallet',
                                                      'bitcoin.tasks.import_addresses',
                                                      'bitcoin.tasks.import_address',
                                                      'bitcoin.tasks.create_refill_chunks']:
            self.blocktrail_subscribe(retval)

    def blocktrail_subscribe(self, txid):
        logger.info('Subscribing to events on {}'.format(txid))
        self.blocktrail_client.subscribe_transaction(identifier='confirmations', transaction=txid, confirmations=1)

    def blocktrail_unsubscribe(self, txid):
        logger.info('Unsubscribing to events on {}'.format(txid))
        try:
            self.blocktrail_client.unsubscribe_transaction(identifier='confirmations', transaction=txid)
        except blocktrail.exceptions.ObjectNotFound:
            logger.info('{} webhook not found'.format(txid))

    def select_chunk(self):
        """
        Select chunk to refill_main_wallet with a locked table to avoid race conditions
        """

        print 'selecting chunks'
        cursor = connection.cursor()
        cursor.execute(query_sql_refill)
        desc = cursor.description
        unspents = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]

        if len(unspents) == 0:
            raise SpoolFundsError('Not enough unspents for transaction')

        chunks = filter(lambda d: d['amount'] == settings.BTC_CHUNK, unspents)
        return chunks


# Initialize federation wallet here
@app.task(base=SpoolAction)
def initialize_federation_wallet():
    logger.info('Resetting the FederationWallet')
    FederationWallet.objects.all().delete()

    # Reset the ids after deleting all the rows
    cursor = connection.cursor()
    cursor.execute("ALTER SEQUENCE bitcoin_federationwallet_id_seq RESTART WITH 1")

    logger.info('Populating federation wallet with unspents')
    unspents = initialize_federation_wallet.transactions.get(settings.BTC_MAIN_WALLET, min_confirmations=1)\
        .get('unspents', [])
    for unspent in unspents:
        if unspent['amount'] in [settings.BTC_TOKEN, settings.BTC_FEE]:
            # main wallet
            unspent.update({'type': 'main'})
            FederationWallet(**unspent).save()

    unspents = initialize_federation_wallet.transactions.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1)\
        .get('unspents', [])
    for unspent in unspents:
        if unspent['amount'] == settings.BTC_CHUNK:
            # main wallet
            unspent.update({'type': 'refill'})
            FederationWallet(**unspent).save()

    logger.info('Finished initializing wallet')


@app.task(base=SpoolAction)
def transaction_monitor(txid, confirmations):
    """
    The monitor needs to:

    1. check if a transaction is confirmed and set the status
    2. check if there are any dependent transactions and push them
    3. clear the ciphertext_wif field if the transaction went through
    """

    logger.info('{} {}'.format(txid, confirmations))
    if confirmations > 0:
        # set transaction status to confirmed
        btc_tx = BitcoinTransaction.objects.get(tx=txid)
        btc_tx.status = TX_CONFIRMED
        btc_tx.save()

        # unsibscribe from blocktrail event
        transaction_monitor.blocktrail_unsubscribe(txid)

        # check for dependent transactions
        logger.info('Checking for dependent transactions...')
        if btc_tx.dependent_tx:
            ownership = btc_tx.dependent_tx.ownership.get(btc_tx=btc_tx.dependent_tx)
            password = crypto.decode(settings.SECRET_KEY, ownership.ciphertext_wif)

            if 'TRANSFER' in btc_tx.dependent_tx.spoolverb:
                # get the password
                transfer.delay(btc_tx.dependent_tx.id, password)
            elif 'UNCONSIGN' in btc_tx.dependent_tx.spoolverb:
                # get the password
                unconsign.delay(btc_tx.dependent_tx.id, password)
            elif 'CONSIGN' in btc_tx.dependent_tx.spoolverb:
                # get the password
                consign.delay(btc_tx.dependent_tx.id, password)
            elif 'LOAN' in btc_tx.dependent_tx.spoolverb:
                # get the password
                if ownership.edition:
                    loan.delay(btc_tx.dependent_tx.id, password)
                else:
                    loan_piece.delay(btc_tx.dependent_tx.id, password)

        # check if password is set in the ownership and remove it
        # this is inside of a try except block because some transactions don't have a ownership mapping
        # e.g. refill transaction
        try:
            ownership = btc_tx.ownership.get(btc_tx=btc_tx)
            if ownership:
                ownership.ciphertext_wif = None
                ownership.save()
        except ObjectDoesNotExist:
            pass


# TODO: Check if we can remove this
@app.task(base=SpoolAction)
def do_transaction(list_signatures):
    task_list = []
    for sig in list_signatures:
        task_list += [sig, monitor.s()]
    res = chain(*task_list)
    return res()


@app.task(base=SpoolAction)
def register(btc_tx_id, password):
    logger.info('register task {}'.format(btc_tx_id))
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    txid = register.spool.register(('', btc_tx.from_address), btc_tx.to_address, btc_tx.file_hash, password,
                                    btc_tx.edition_num, min_confirmations=1, sync=False, ownership=False)
    logger.info('Registering: {}'.format(txid))
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = register.transactions._service.name
    btc_tx.save()
    return txid


@app.task(base=SpoolAction)
def consigned_registration(btc_tx_id, password):
    logger.info('consigned registration task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    txid = consigned_registration.spool.consigned_registration(('', btc_tx.from_address), btc_tx.to_address,
                                                               btc_tx.file_hash, password,
                                                               min_confirmations=1, sync=False, ownership=False)
    logger.info('Consigned Registration: {}'.format(txid))
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = consigned_registration.transactions._service.name
    btc_tx.save()
    return txid


@app.task(base=SpoolAction)
def register_piece(btc_tx_id, password):
    logger.info('register_piece task {}'.format(btc_tx_id))
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    txid = register_piece.spool.register_piece(('', btc_tx.from_address), btc_tx.to_address, btc_tx.file_hash, password,
                                               min_confirmations=1, sync=False, ownership=False)
    logger.info('Registering piece: {} {}'.format(btc_tx.id, txid))
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = register_piece.transactions._service.name
    btc_tx.save()
    return txid


@app.task(base=SpoolAction)
def editions(btc_tx_id, password):
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    txid = editions.spool.editions(('', btc_tx.from_address), btc_tx.to_address, btc_tx.file_hash, password,
                                    btc_tx.num_editions, min_confirmations=1, sync=False, ownership=False)
    logger.info('Registering number of editions: {}'.format(txid))
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = editions.transactions._service.name
    btc_tx.save()
    return txid


@app.task(base=SpoolAction)
def refill(btc_tx_id, password):
    logger.info('refill task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    ntokens = len(btc_tx.outputs) - 1
    txid = refill.spool.refill(('', btc_tx.from_address), btc_tx.to_address, 1, ntokens, password,
                                min_confirmations=1, sync=False)
    logger.info('Refill {}'.format(txid))
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = refill.transactions._service.name
    btc_tx.save()
    return txid


@app.task(base=SpoolAction)
def transfer(btc_tx_id, password):
    logger.info('transfer task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    from_address = tuple(btc_tx.from_address.split(':'))
    txid = transfer.spool.transfer(from_address, btc_tx.to_address, btc_tx.file_hash, password,
                                   btc_tx.edition_num, min_confirmations=1, sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = transfer.transactions._service.name
    btc_tx.save()
    logger.info('Transfering edition: {} {}'.format(btc_tx.id, txid))
    return txid


@app.task(base=SpoolAction)
def consign(btc_tx_id, password):
    logger.info('consign task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    from_address = tuple(btc_tx.from_address.split(':'))
    txid = consign.spool.consign(from_address, btc_tx.to_address, btc_tx.file_hash, password,
                                 btc_tx.edition_num, min_confirmations=1, sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = consign.transactions._service.name
    btc_tx.save()
    logger.info('Consigning edition: {} {}'.format(btc_tx.id, txid))
    return txid


@app.task(base=SpoolAction)
def unconsign(btc_tx_id, password):
    logger.info('unconsign task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    from_address = tuple(btc_tx.from_address.split(':'))
    txid = unconsign.spool.unconsign(from_address, btc_tx.to_address, btc_tx.file_hash, password,
                                     btc_tx.edition_num, min_confirmations=1, sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = unconsign.transactions._service.name
    btc_tx.save()
    logger.info('Unconsigning edition: {} {}'.format(btc_tx.id, txid))
    return txid


@app.task(base=SpoolAction)
def loan(btc_tx_id, password):
    logger.info('loan task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    from_address = tuple(btc_tx.from_address.split(':'))
    txid = loan.spool.loan(from_address, btc_tx.to_address, btc_tx.file_hash, password,
                           btc_tx.edition_num, btc_tx.loan_start, btc_tx.loan_end,
                           min_confirmations=1, sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = loan.transactions._service.name
    btc_tx.save()
    logger.info('Loaning edition: {} {}'.format(btc_tx.id, txid))
    return txid


@app.task(base=SpoolAction)
def loan_piece(btc_tx_id, password):
    logger.info('loan_piece task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    from_address = tuple(btc_tx.from_address.split(':'))
    txid = loan.spool.loan(from_address, btc_tx.to_address, btc_tx.file_hash, password,
                           btc_tx.edition_num, btc_tx.loan_start, btc_tx.loan_end,
                           min_confirmations=1, sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = loan.transactions._service.name
    btc_tx.save()
    logger.info('Loaning piece: {} {}'.format(btc_tx.id, txid))
    return txid


@app.task(base=SpoolAction)
def migrate(btc_tx_id, password):
    logger.info('migrate task')
    btc_tx = BitcoinTransaction.objects.get(id=btc_tx_id)
    txid = migrate.spool.migrate(('', btc_tx.from_address), btc_tx.old_address, btc_tx.to_address,
                                 btc_tx.file_hash, password, btc_tx.edition_num, min_confirmations=1,
                                 sync=False, ownership=False)
    btc_tx.status = TX_UNCONFIRMED
    btc_tx.tx = txid
    btc_tx.service_str = migrate.transactions._service.name
    btc_tx.save()
    logger.info('Migrating edition: {} {}'.format(btc_tx.id, txid))
    return txid


# TODO: Check if we can remove this
@app.task(base=SpoolAction, bind=True, max_retries=None)
def monitor(self, txid):
    # accepts a list of transactions to monitor.
    # for instance in register + refill it will only return once both are registered in the blockhain
    txid = [txid] if not isinstance(txid, list) else txid

    logger.info('Monitoring: {}'.format(txid))
    confirmations = []
    for tx in txid:
        conf = monitor.transactions.get(tx).get('confirmations', 0)
        conf = 0 if conf == '' else conf
        confirmations.append(conf)
    if sum(confirmations) < len(txid):
        raise self.retry(countdown=TIMEOUT)
    logger.info('BTC registered {}'.format(txid))
    for tx in txid:
        btc_tx = BitcoinTransaction.objects.get(tx=tx)
        btc_tx.status = TX_CONFIRMED
        btc_tx.save()


@app.task(base=SpoolAction)
def refill_main_wallet():
    inputs = refill_main_wallet.select_chunk()
    outputs = [{'address': BitcoinWallet.mainAdminBtcAddress(), 'value': settings.BTC_FEE}] * 50
    outputs += [{'address': BitcoinWallet.mainAdminBtcAddress(), 'value': settings.BTC_TOKEN}] * 150
    unsigned_tx = refill_main_wallet.transactions.build_transaction(inputs, outputs)
    signed_tx = refill_main_wallet.transactions.sign_transaction(unsigned_tx, settings.BTC_REFILL_PASSWORD)
    txid = refill_main_wallet.transactions.push(signed_tx)
    logger.info('Refilling main wallet {}'.format(txid))

    return txid


@app.task
def analyser(exc, task_id, args, kwargs, einfo):
    logger.info('task failed {}'.format(task_id))
    # TODO: Log exception
    print exc


@app.task(base=SpoolAction)
def create_refill_chunks():
    unsigned_tx = create_refill_chunks.transactions.simple_transaction(settings.BTC_REFILL_ADDRESS,
                                                                       [(settings.BTC_REFILL_ADDRESS,
                                                                         settings.BTC_CHUNK)] * 5,
                                                                       min_confirmations=1)
    signed_tx = create_refill_chunks.transactions.sign_transaction(unsigned_tx, settings.BTC_REFILL_PASSWORD)
    txid = create_refill_chunks.transactions.push(signed_tx)
    return txid


@app.task
def send_low_funds_email(sum_unspents):
    msg = """
    The BTC_REFILL_ADDRESS {} is running low on funds. It currently has {} btc.
    Please send funds to this address.
    """.format(settings.BTC_REFILL_ADDRESS, sum_unspents * 0.00000001)

    warn_ascribe_devel('Ascribe refill wallet funds low', msg)


# @periodic_task(run_every=timedelta(hours=1))
def check_status():
    """
    Checks the status of the federation and refill wallet every hour.
    Actions performed:

    1. In the refill wallets create refill chunks of 2 160 000 satoshi if number of chunks:
        - 50 * 30000 (fee) + 150 * 3000 (token) + 210 000 (tx fee)
        - if number of refill chunks < 10 create 5 chunks

    2. Refill federation wallet if num fees < 500 or num tokens < 1500:
        - refill with 2 refill chunks

    3. If refill wallet < 0.3 bitcoin which is approximately 10 refill chunks
        - Send email warning of low funds in the Refill wallet
        - Ask trent for das money
    """
    # We cannot use base=SpoolAction because it does not work with periodic tasks
    transactions = Transactions(service=settings.BTC_SERVICE, testnet=settings.BTC_TESTNET,
                                username=settings.BTC_USERNAME, password=settings.BTC_PASSWORD,
                                host=settings.BTC_HOST, port=settings.BTC_PORT)

    # check refill wallet
    logger.info('checking refill wallet')
    unspents = transactions.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
    refill_chunks = filter(lambda d: d['amount'] == settings.BTC_CHUNK, unspents)
    if len(refill_chunks) < 10:
        # create_refill_chunks -> create 5 refill_chunks
        logger.info('refill wallet low on refill chunks. Creating ...')
        txid = create_refill_chunks.delay()
        logger.info(txid)

    unspents = transactions.get(settings.BTC_REFILL_ADDRESS, min_confirmations=1).get('unspents', [])
    sum_unspents = sum([u['amount'] for u in unspents])
    if sum_unspents < 30000000:
        # TODO: we don't want this to be sent every hour, maybe
        logger.info('funds low in refill wallet. Sending email...')
        send_low_funds_email.delay(sum_unspents)

    # check federation wallet
    unspents = transactions.get(settings.BTC_MAIN_WALLET, min_confirmations=1).get('unspents', [])
    fees = filter(lambda d: d['amount'] == settings.BTC_FEE, unspents)
    tokens = filter(lambda d: d['amount'] == settings.BTC_TOKEN, unspents)
    if len(fees) < 500 or len(tokens) < 1500:
        # refill federation wallet x 10 times if we have chunks
        logger.info('federation wallet low on funds. Refilling...')
        for _ in range(min(2, len(refill_chunks))):
            refill_main_wallet.delay()
        initialize_federation_wallet.delay()


@app.task(base=SpoolAction)
def initialize():
    """
    Task to be performed when the app is restarted:

    1. Check unconfirmed transactions
        - We may have missed some events from blocktrail
    2. Push passed transactions
        - Maybe BTC was disabled and now we want to push past transactions
    3. Import all addresses
    """
    logger.info('Performing initialization of the bitcoin layer...')

    # import all addresses
    from bitcoin.management.commands.import_addresses import import_addresses
    import_addresses.delay()

    # this should only be done for transactions created after this code went live
    # we will remove this once we are sure that everything is ok in the database
    from_datetime = timezone.datetime.strptime('2015-11-04 10:00:00',
                                               '%Y-%m-%d %H:%M:%S')
    from_datetime = timezone.make_aware(from_datetime, timezone=timezone.utc)

    # check if we are using the mainnet or testnet
    # testnet addresses start with 'm' or 'n'
    # mainnet addrresses start with '1'
    if settings.BTC_TESTNET:
        regex = r'^([mn]|\S+?:[mn])\S+?'
    else:
        regex = r'^(1|\S+?:1)\S+?'

    # Check unconfirmed transactions
    logger.info('Checking unconfirmed transactions...')
    for tx in BitcoinTransaction.objects.filter(status=TX_UNCONFIRMED, datetime__gt=from_datetime)\
            .filter(from_address__regex=regex).order_by('datetime'):
        try:
            logger.info('Checking transaction {}'.format(tx.id))
            response = initialize.blocktrail_client.transaction(tx.tx)
            confirmations = response.get('confirmations', 0)
            if confirmations > 0:
                transaction_monitor.delay(tx.tx, confirmations)
        except blocktrail.exceptions.ObjectNotFound:
            tx.error_msg = 'Transaction not found'
            tx.status = TX_REJECTED
            tx.save()
            logger.info('Transaction {} not found.'.format(tx.tx))

    # Push passed transactions
    logger.info('Checking unpushed transactions...')
    # First we need get pending transactions in the queue and exclude them or else we are
    # going to send duplicate transactions
    tx_id_regex = r'^\((\d+),\s\S+?\)'
    tx_ids_exclude = []

    scheduled_tasks = app.control.inspect().scheduled()
    scheduled_tasks = scheduled_tasks if scheduled_tasks else {}
    active_tasks = app.control.inspect().active()
    active_tasks = active_tasks if active_tasks else {}
    reserved_tasks = app.control.inspect().reserved()
    reserved_tasks = reserved_tasks if reserved_tasks else {}
    for queue, tasks in scheduled_tasks.iteritems():
        for task in tasks:
            request = task.get('request', None)
            if request:
                match = re.match(tx_id_regex, request.get('args', ''))
                if match:
                    logger.info('Found transaction {} in the queue'.format(match.groups()[0]))
                    tx_ids_exclude.append(int(match.groups()[0]))

    for queue, tasks in active_tasks.iteritems():
        for task in tasks:
            request = task.get('request', None)
            if request:
                match = re.match(tx_id_regex, request.get('args', ''))
                if match:
                    logger.info('Found transaction {} in the queue'.format(match.groups()[0]))
                    tx_ids_exclude.append(int(match.groups()[0]))

    for queue, tasks in reserved_tasks.iteritems():
        for task in tasks:
            request = task.get('request', None)
            if request:
                match = re.match(tx_id_regex, request.get('args', ''))
                if match:
                    logger.info('Found transaction {} in the queue'.format(match.groups()[0]))
                    tx_ids_exclude.append(int(match.groups()[0]))

    for tx in BitcoinTransaction.objects.filter(status=TX_PENDING, datetime__gt=from_datetime)\
            .filter(from_address__regex=regex).exclude(id__in=tx_ids_exclude).order_by('datetime'):

        logger.info('Pushing unpushed transaction {}'.format(tx.id))
        # Get the ownership action
        try:
            if tx.spoolverb == 'ASCRIBESPOOL01FUEL':
                action = None
            else:
                action = Ownership.objects.get(btc_tx=tx).type
        except Ownership.DoesNotExist:
            tx.error_msg = 'Ownership not found for this transaction.'
            tx.status = TX_REJECTED
            tx.save()
            logger.info('Ownership not found for transaction {}'.format(tx.tx))
        except Ownership.MultipleObjectsReturned:
            tx.error_msg = 'Multiple ownership objects returned for this transaction.'
            tx.status = TX_REJECTED
            tx.save()
            logger.info('Multiple ownership objects returned for transaction {}'.format(tx.tx))
        else:

            if action == 'OwnershipPiece':
                register_piece.delay(tx.id, util.mainAdminPassword())
            elif action == 'OwnershipEditions':
                editions.delay(tx.id, util.mainAdminPassword())
            elif action == 'OwnershipRegistration':
                register.delay(tx.id, util.mainAdminPassword())
            elif action == 'OwnershipTransfer':
                # Transfers are trigered by refill. Once we push a refill
                # the transfer will go through
                pass
            elif action == 'Consignment':
                # Consignments are trigered by refill. Once we push a refill
                # the consignment will go through
                pass
            elif action == 'UnConsignment':
                # Unconsignments are trigered by refill. Once we push a refill
                # the unconsignment will go through
                pass
            elif action == 'Loan':
                # Loans are trigered by refill. Once we push a refill
                # the loan will go through
                pass
            elif action == 'LoanPiece':
                # Loans of pieces are trigered by refill. Once we push a refill
                # the loan of the piece will go through
                pass
            elif action == 'ConsignedRegistration':
                consigned_registration.delay(tx.id, util.mainAdminPassword())
            elif action == 'OwnershipMigration':
                migrate.delay(tx.id, util.mainAdminPassword())
            elif tx.spoolverb == 'ASCRIBESPOOL01FUEL':
                refill.delay(tx.id, util.mainAdminPassword())


def get_all_addresses():
    if settings.BTC_TESTNET:
        regex = r'^([mn]|\S+?:[mn])\S+?'
    else:
        regex = r'^(1|\S+?:1)\S+?'

    # get piece addresses
    for p in Piece.objects.filter(bitcoin_path__regex=regex):
        if p.bitcoin_path:
            yield (p.bitcoin_id, p.user_registered.email)
        continue

    # get edition addresses
    for e in Edition.objects.filter(bitcoin_path__regex=regex):
        yield (e.bitcoin_id, e.owner.email)

    for o in Ownership.objects.filter(prev_btc_address__regex=regex, new_btc_address__regex=regex):
        if o.prev_btc_address is not None:
            yield(o.prev_btc_address.split(':')[-1], o.prev_owner.email)
        if o.new_btc_address is not None:
            yield(o.new_btc_address.split(':')[-1], o.new_owner.email)


@app.task(base=SpoolAction)
def import_addresses():
    """
    Imports all addresses in the database
    """

    logger.info('Importing addresses...')
    # TODO: Use celery.group and execute on import_address in this file
    for address, user_email in get_all_addresses():
        try:
            import_addresses.transactions.import_address(address, account=user_email, rescan=False)
        except Exception as e:
            if e.message == {u'message': u'Invalid Bitcoin address or script', u'code': -5}:
                logger.info('Invalid address in import_addresses {}'.format(address))
            else:
                raise


@app.task(base=SpoolAction, ignore_result=False)
def import_address(address, account):
    try:
        if settings.BTC_ENABLED:
            import_address.transactions.import_address(address.split(':')[-1], account)
    except Exception as e:
        # NOTE: Sometimes, this message is thrown even though you're actually importing
        # a 'valid' bitcoin address.
        # Bitcoin however prefixes testnet addresses differently than mainnet addresses.
        # So if you're using an account that has been created on live (with a mainnet
        # Cryptowallet, this account's Bitcoin addresses will trigger this exception.
        # To still be able to test, just create an account on staging.
        if e.message == {u'message': u'Invalid Bitcoin address or script', u'code': -5}:
            logger.info('Invalid address in import_address {} {}'.format(address, account))
        else:
            raise
    return address
