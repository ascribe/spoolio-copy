from __future__ import absolute_import

from whitelabel.ikonotv.models import WhitelabelIkonotvFactory


class APIUtilWhitelabelIkonotv(object):
    @staticmethod
    def create_whitelabel_ikonotv(user):
        return WhitelabelIkonotvFactory.create(user)
