__author__ = 'sarahleu'


EQ_TXSIZE = (10, 148, 34)


class BitcoinService(object):

    # minimum payment for a transactions. In satoshi. A bit arbitrary.
    minTransactionSize = 10000

    # minimum tx accepted by blockr.io
    minDustSize = 600

    # maximum transaction fee
    maxTransactionFee = 50000

    # minimum mining fee
    minTransactionFee = 10000

    @staticmethod
    def calc_tx_size(nb_inputs, nb_outputs):
        return (EQ_TXSIZE[0] +
                EQ_TXSIZE[1] * nb_inputs +
                EQ_TXSIZE[2] * nb_outputs)
