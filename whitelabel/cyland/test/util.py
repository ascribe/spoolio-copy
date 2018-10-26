from __future__ import absolute_import

from whitelabel.cyland.models import WhitelabelCylandFactory


class APIUtilWhitelabelCyland(object):
    @staticmethod
    def create_whitelabel_cyland(user):
        return WhitelabelCylandFactory.create(user)
