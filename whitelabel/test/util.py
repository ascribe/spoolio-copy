from __future__ import absolute_import

from whitelabel.market.models import WhitelabelMarketFactory


class APIUtilWhitelabel(object):
    @staticmethod
    def create_whitelabel_market(user, amount=1, subdomain='market', name='market_name', title='market_title',
                                 logo='market_logo'):
        if amount > 1:
            return [WhitelabelMarketFactory.create(user,
                                                   subdomain + str(i),
                                                   name + str(i),
                                                   title + str(i),
                                                   logo) for i in range(amount)]
        return WhitelabelMarketFactory.create(user, subdomain, name, title, logo)
