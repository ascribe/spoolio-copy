import ast
import traceback

from django.contrib.auth.models import User
from django.db import models
from django.utils.datetime_safe import datetime

from pycoin.key.BIP32Node import BIP32Node
from pycoin.encoding import EncodingError

import pytz
from util import crypto

from util.models import BackendException

from util import util
from bitcoin import btc_util
from bitcoin.bitcoin_service import BitcoinService
from users.models import Role
from django.conf import settings

TX_PENDING, TX_UNCONFIRMED, TX_CONFIRMED, TX_REJECTED = 0, 1, 2, 3

TX_STATUS_CHOICES = ((TX_PENDING, 'Pending'),
                     (TX_UNCONFIRMED, 'Unconfirmed'),
                     (TX_CONFIRMED, 'Confirmed'),
                     (TX_REJECTED, 'Rejected'),)


class FederationWallet(models.Model):
    class Meta:
        app_label = 'bitcoin'

    amount = models.IntegerField()
    confirmations = models.IntegerField()
    vout = models.IntegerField()
    txid = models.TextField()
    type = models.CharField(max_length=100, default='')

    # TODO seems to be unused - if so, remove
    @property
    def unspent(self):
        return {'amount': self.amount,
                'confirmations': self.confirmations,
                'txid': self.txid,
                'vout': self.vout}


class BitcoinTransaction(models.Model):
    class Meta:
        app_label = 'bitcoin'

    datetime = models.DateTimeField(auto_now_add=True)
    service_str = models.CharField(max_length=50, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True, related_name='tx_created')

    from_address = models.CharField(max_length=100)
    inputs_str = models.TextField(blank=True, null=True)
    outputs_str = models.TextField(blank=True, null=True)
    mining_fee = models.IntegerField(blank=True, null=True)
    tx = models.TextField(max_length=100, blank=True, null=True)

    block_height = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(choices=TX_STATUS_CHOICES, default=TX_PENDING, blank=True, null=True)
    spoolverb = models.CharField(max_length=40, blank=True, null=True)
    dependent_tx = models.ForeignKey('self', null=True, default=None)

    error_msg = models.TextField(blank=True, null=True)

    inputs_blacklist = []

    @classmethod
    def register(cls, ownership):
        # TODO: change name to register_edition

        # set the addresses
        ownership.new_btc_address = ownership.edition.bitcoin_path
        ownership.prev_btc_address = BitcoinWallet.mainAdminBtcAddress()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.edition.hash_as_address()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.edition.owner,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.register)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def consigned_registration(cls, ownership):
        # set the addresses
        ownership.new_btc_address = ownership.piece.bitcoin_path
        ownership.prev_btc_address = BitcoinWallet.mainAdminBtcAddress()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.piece.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.piece.hash_as_address()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.consigned_registration)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def register_piece(cls, ownership):
        # set the addresses
        ownership.new_btc_address = ownership.piece.bitcoin_path
        ownership.prev_btc_address = BitcoinWallet.mainAdminBtcAddress()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.piece.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.piece.hash_as_address()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.piece)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def editions(cls, ownership):
        # TODO: change name to register_num_editions
        # set the addresses
        ownership.new_btc_address = ownership.piece.bitcoin_path
        ownership.prev_btc_address = BitcoinWallet.mainAdminBtcAddress()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.piece.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.piece.hash_as_address()),
                   (BitcoinService.minDustSize, ownership.piece.bitcoin_id)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.editions)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def transfer(cls, ownership):
        # if new owner has to register skip
        if not Role.objects.filter(user=ownership.new_owner, type='UserNeedsToRegisterRole'):

            # set the addresses
            if not ownership.prev_btc_address:
                ownership.prev_btc_address = ownership.edition.btc_owner_address
            if not ownership.new_btc_address:
                ownership.new_btc_address = BitcoinWallet.walletForUser(ownership.new_owner).create_new_address()
                BitcoinWallet.import_address(ownership.new_btc_address, ownership.new_owner).delay()

            # set the outputs
            outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                       (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

            # create the transaction
            transaction = cls(user=ownership.prev_owner,
                              from_address=ownership.prev_btc_address,
                              outputs=outputs,
                              spoolverb=ownership.spoolverb.transfer)
            transaction.save()

            # link the transaction to the ownership
            ownership.btc_tx = transaction
            ownership.save()

            return transaction

    @classmethod
    def consign(cls, ownership):
        # set the addresses
        if not ownership.prev_btc_address:
            ownership.prev_btc_address = ownership.edition.btc_owner_address
        if not ownership.new_btc_address:
            ownership.new_btc_address = BitcoinWallet.walletForUser(ownership.new_owner).create_new_address()
            BitcoinWallet.import_address(ownership.new_btc_address, ownership.new_owner).delay()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.prev_owner,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.consign)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def unconsign(cls, ownership):
        # set the addresses
        # the addresses are set a this point

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.prev_owner,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.unconsign)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def loan(cls, ownership):
        # set the addresses
        if not ownership.prev_btc_address:
            ownership.prev_btc_address = ownership.edition.btc_owner_address
        if not ownership.new_btc_address:
            ownership.new_btc_address = BitcoinWallet.walletForUser(ownership.new_owner).create_new_address()
            BitcoinWallet.import_address(ownership.new_btc_address, ownership.new_owner).delay()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.loan)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def loan_piece(cls, ownership):
        # set the addresses

        if not ownership.prev_btc_address:
            ownership.prev_btc_address = ownership.piece.bitcoin_id
        if not ownership.new_btc_address:
            ownership.new_btc_address = BitcoinWallet.walletForUser(ownership.new_owner).create_new_address()
            BitcoinWallet.import_address(ownership.new_btc_address, ownership.new_owner).delay()

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.piece.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=ownership.prev_btc_address,
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.loan)
        transaction.save()

        # link the transaction to the ownership
        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def migrate(cls, ownership):
        # set the addresses
        # addresses are already set at this point

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.edition.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.from_piece_address_noPrefix),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.edition.owner,
                          from_address=BitcoinWallet.mainAdminBtcAddress(),
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.migrate)
        transaction.save()

        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def migrate_piece(cls, ownership):
        # set the addresses
        # addresses are already set at this point

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.piece.hash_as_address_no_metada()),
                   (BitcoinService.minDustSize, ownership.from_piece_address_noPrefix),
                   (BitcoinService.minDustSize, ownership.to_piece_address_noPrefix)]

        # create the transaction
        transaction = cls(user=ownership.piece.user_registered,
                          from_address=BitcoinWallet.mainAdminBtcAddress(),
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.migrate)
        transaction.save()

        ownership.btc_tx = transaction
        ownership.save()

        return transaction

    @classmethod
    def refill(cls, ownership):
        # set the addresses
        # addresses are already set at this point

        # set the outputs
        outputs = [(BitcoinService.minDustSize, ownership.from_piece_address_noPrefix),
                   (BitcoinService.minDustSize, ownership.from_piece_address_noPrefix),
                   (BitcoinService.minTransactionFee, ownership.from_piece_address_noPrefix)]

        # check it the refill is for an edition or a piece loan
        user = ownership.edition.owner if ownership.edition else ownership.piece.user_registered

        # create the transaction
        transaction = cls(user=user,
                          from_address=BitcoinWallet.mainAdminBtcAddress(),
                          outputs=outputs,
                          spoolverb=ownership.spoolverb.fuel)
        transaction.save()

        # link the transaction to the ownership
        # we do not store the refills in the ownership table

        return transaction

    @property
    def to_address(self):
        return self.outputs[-1][1]

    @property
    def old_address(self):
        # only used for migrations
        return self.outputs[1][1]

    @property
    def file_hash(self):
        return self.outputs[0][1], self.outputs[1][1]

    @property
    def edition_num(self):
        ownership = self.ownership.get(btc_tx=self)
        return ownership.edition.edition_number if ownership.edition else 0

    @property
    def num_editions(self):
        return self.ownership.get(btc_tx=self).piece.num_editions

    @property
    def loan_start(self):
        ownership = self.ownership.get(btc_tx=self)
        return ownership.datetime_from.strftime('%y%m%d')

    @property
    def loan_end(self):
        ownership = self.ownership.get(btc_tx=self)
        return ownership.datetime_to.strftime('%y%m%d')

    @classmethod
    def create(cls,
               user=None,
               from_address=None,
               from_wallet=None,
               inputs=None,
               outputs=None,
               mining_fee=None,
               tx=None,
               block_height=None,
               status=None,
               spoolverb=None):

        assert not (from_address is None and from_wallet is None)
        assert outputs is not None

        if from_address is None:
            from_address = BitcoinTransaction.get_wallet(from_address, user).address

        outputs = BitcoinTransaction.as_dict(outputs)

        if status is None:
            status = TX_PENDING
        # if spoolverb:
        #    assert len(spoolverb) >= 19, "avoid odd-length string in pybitcointools.mktx()"

        transaction = cls(user=user,
                          from_address=from_address,
                          inputs_str=str(inputs),
                          outputs_str=str(outputs),
                          mining_fee=mining_fee,
                          tx=tx,
                          block_height=block_height,
                          status=status,
                          spoolverb=spoolverb
                          )
        transaction.service_str = "BitcoinDaemonMainnetService"
        return transaction

    @property
    def inputs(self):
        return ast.literal_eval(self.inputs_str) if (self.inputs_str and self.inputs_str != 'None') else None

    @inputs.setter
    def inputs(self, value):
        self.inputs_str = str(value)

    @property
    def outputs(self):
        return ast.literal_eval(self.outputs_str) if (self.outputs_str and self.outputs_str != 'None') else None

    @outputs.setter
    def outputs(self, value):
        self.outputs_str = str(value)

    @property
    def from_wallet(self):
        return BitcoinTransaction.get_wallet(self.from_address, self.user)

    @staticmethod
    def get_wallet(from_address, user):
        return BitcoinWallet.mainAdminWallet() if (from_address == settings.BTC_MAIN_WALLET) \
            else BitcoinWallet.walletForUser(user)

    @property
    def leaf_address(self):
        return self.from_address if ":" in self.from_address else None

    @property
    def spoolverb_hex(self):
        if self.spoolverb:
            return "6a%x%s" % (len(self.spoolverb), self.spoolverb.encode('hex'))
        return None

    @property
    def tx_hex(self):
        return self.tx

    @property
    def size(self):
        """
        http://bitcoinfees.com/
        """
        return BitcoinService.calc_tx_size(len(self.inputs), len(self.outputs) + 1)

    @staticmethod
    def as_dict(io):
        if isinstance(io, basestring):
            try:
                io = ast.literal_eval(io)
            except ValueError, e:
                print e.message
                print "String = %s" % io
                return None
        if len(io) > 0 and isinstance(io[0], dict):
            return io
        return [{'value': value, 'address': to_address} for (value, to_address) in io]


class BitcoinWallet(models.Model):
    """
    Implements an HD-wallet (BIP0032) based upon the pycoin library
    """
    class Meta:
        app_label = 'bitcoin'

    user = models.ForeignKey(User, blank=True, null=True)
    public_key = models.CharField(max_length=200)

    def __unicode__(self):
        return unicode('Public wallet of user %s' % self.user)

    @classmethod
    def create(cls, user, public_key=None, password=None, service=None):

        if not public_key and password:
            public_key = cls.pubkeyFromPassword(user, password)

        bitcoin_wallet = cls(user=user,
                             public_key=public_key)
        if service:
            bitcoin_wallet.service = service
        return bitcoin_wallet

    @staticmethod
    def encoded_wif_for_path(ownership, password):
        if ownership.prev_btc_address:
            path, prev_address = ownership.prev_btc_address.split(':')
        elif ownership.edition:
            path, prev_address = ownership.edition.btc_owner_address.split(':')
        else:
            if not ownership.piece.bitcoin_path:
                new_address = BitcoinWallet.walletForUser(ownership.piece.user_registered).create_new_address()
                BitcoinWallet.import_address(new_address, ownership.piece.user_registered).delay()
                ownership.piece.bitcoin_path = new_address
                ownership.piece.save()
            path, prev_address = ownership.piece.bitcoin_path.split(':')

        wallet = BitcoinWallet.pycoinWallet(password=BitcoinWallet.pycoinPassword(ownership.prev_owner, password),
                                            public=False)
        wif = wallet.subkey_for_path(path).wif()
        encoded_wif = crypto.encode(settings.SECRET_KEY, wif)
        return encoded_wif

    @staticmethod
    def pycoinWallet(public_key=None, public=True, testnet=settings.BTC_TESTNET, password=None):
        netcode = 'XTN' if testnet else 'BTC'
        if public:
            return BIP32Node.from_wallet_key(public_key)
        else:
            assert not password is None
            return BIP32Node.from_master_secret(password, netcode=netcode)

    @staticmethod
    def pubkeyFromPassword(user, password):
        prv_wallet = BitcoinWallet.pycoinWallet(password=BitcoinWallet.pycoinPassword(user, password), public=False)
        if user == util.mainAdminUser():
            assert prv_wallet.bitcoin_address() == settings.BTC_MAIN_WALLET, \
                "Admin wallet computes to %s, not %s" % (prv_wallet.bitcoin_address(), settings.BTC_MAIN_WALLET)
        return prv_wallet.wallet_key(as_private=False)

    @property
    def rootAddress(self):
        root_address = self.pycoinWallet(public_key=self.public_key).bitcoin_address()
        assert ':' not in root_address
        return root_address

    @property
    def address(self):
        return self.pycoinWallet(public_key=self.public_key).bitcoin_address()

    def create_new_address(self):
        """
        Creates a bitcoin address in a non-blocking fashion, without importing it into
        the bitcoin daemon.
        """
        path = btc_util._uniqueHierarchicalString()
        # the new address is not a "pure" bitcoin address; it has the path in front
        #  -storing as one string makes life much easier everywhere else. Only btc
        #   transactions need to split them apart, which is easy.
        address = BitcoinWallet.pycoinWallet(public_key=self.public_key).subkey_for_path(path).bitcoin_address()
        new_address = '%s:%s' % (path, address)
        return new_address

    def create_new_addresses(self, num_addresses):
        """
        Creates a number of bitcoin addresses in a non-blocking fashion, without importing them into
        the bitcoin daemon.
        """
        return [self.create_new_address() for _ in xrange(num_addresses)]

    @staticmethod
    def import_address(address, user):
        """
        Proxy for bitcoin.tasks's import_address that actually only
        returns a signature/tasks that can later be executed.
        """
        from bitcoin.tasks import import_address
        return import_address.si(address, user.email)

    @staticmethod
    def import_addresses(addresses, user):
        """
        Same as import_address, but takes multiple addresses as input
        and returns a list of signatures/tasks.
        """
        return [BitcoinWallet.import_address(address, user) for address in addresses]

    @staticmethod
    def walletForRootAddress(address):
        # TODO: slow query
        return [w for w in BitcoinWallet.objects.filter() if w.address == address]

    @staticmethod
    def walletForUser(user):
        return BitcoinWallet.objects.get(user=user)

    @staticmethod
    def pycoinPassword(user, password):
        # check if password is a wif. It it is return it witouth appending the email
        try:
            BIP32Node.from_text(password)
            return password
        except EncodingError:
            # backwards compatibility for collision of public wallets with same password
            if user.date_joined > datetime(2014, 12, 15).replace(tzinfo=pytz.UTC) \
                    and not user == util.mainAdminUser():
                return password + user.email
            return password

    # ====================================================
    # admin-btc
    @staticmethod
    def mainAdminBtcAddress():
        return BitcoinWallet.mainAdminWallet().rootAddress

    @staticmethod
    def mainAdminWallet():
        return BitcoinWallet.walletForUser(user=util.mainAdminUser())
