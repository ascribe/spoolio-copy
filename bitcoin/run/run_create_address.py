import pycoin.wallet
from string import digits, ascii_uppercase, ascii_lowercase

def randomStr(n, chars=None):
    if chars is None:
        chars = digits + ascii_uppercase + ascii_lowercase
    return ''.join([random.choice(chars) for i in xrange(n)])

import random
while(True):
    password = randomStr(random.randint(8, 40))
    prv_wallet = pycoin.wallet.Wallet.from_master_secret(password)
    addr = prv_wallet.bitcoin_address()
    if addr[1:5].lower() in ['rodo']\
            or addr[1:6].lower() in ['ascri', 'ascr1', 'trent', 'bruce', 'sarah', 'masha', 'eyeem']:
        print addr
        print password
        with open('wallet', 'a') as fid:
            fid.write("\n" + addr + "\n" + password + "\n")
        break
