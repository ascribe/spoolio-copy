from bitcoin.bitcoin_service import BitcoinService
from django.test import TestCase

from bitcoin.models import BitcoinWallet, BitcoinTransaction
from users.test.util import APIUtilUsers

from django.conf import settings

__author__ = 'dimi'

BTC_TEST_ADDRESS = '1AKdkzQDjbNQeQhWBVcHywfS9vynWoTLBM'


class BitcoinWalletTestCase(TestCase, APIUtilUsers):
    def setUp(self):
        """
        generate user data
        """
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')

        # delete all wallets so not to interfer with the tests
        BitcoinWallet.objects.all().delete()

    def testCreateBitcoinWallet(self):
        save_wallet = BitcoinWallet.create(self.user1, password=self.password)
        save_wallet.save()

        find_wallet = BitcoinWallet.objects.get(user=self.user1.id)
        self.assertTrue(save_wallet == find_wallet)

    def testUpdateBitcoinWallet(self):
        save_wallet = BitcoinWallet.create(self.user1, password=self.password)
        save_wallet.save()
        save_wallet.public_key = "nonsense"
        save_wallet.save()

        find_wallet = BitcoinWallet.objects.get(user=self.user1.id)
        self.assertTrue(save_wallet == find_wallet)
        self.assertEqual(find_wallet.public_key, "nonsense")

    def testPycoinWallet(self):
        save_wallet = BitcoinWallet.create(self.user_admin, password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        save_wallet.save()

        find_wallet = BitcoinWallet.objects.get(user=self.user_admin.id)
        self.assertEqual(find_wallet.rootAddress,
                         find_wallet.pycoinWallet(public_key=find_wallet.public_key).bitcoin_address())


class BitcoinTransactionTestCase(TestCase, APIUtilUsers):
    def setUp(self):
        """
        generate user data
        """
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')

    def testCreateBitcoinTransaction(self):
        user = self.user1
        from_wallet = BitcoinWallet.create(self.user1, password=self.password)
        from_wallet.save()

        save_bitcointransaction = BitcoinTransaction.create(user=user,
                                                            from_address=from_wallet.address,
                                                            outputs=[(int(1 * BitcoinService.minTransactionSize),
                                                                      BTC_TEST_ADDRESS)],
                                                            spoolverb='ascribespoolverbtest'
                                                            )
        save_bitcointransaction.save()

        find_bitcointransaction = BitcoinTransaction.objects.get(id=save_bitcointransaction.id)
        self.assertTrue(save_bitcointransaction == find_bitcointransaction)
