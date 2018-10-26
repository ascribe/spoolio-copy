
from whitelabel.filters import SubmittedPieceFilter
from whitelabel.models import WhitelabelSettings


class IkonotvSubmittedPieceFilter(SubmittedPieceFilter):

    def __init__(self, *args, **kwargs):
        try:
            ikonotv_admin = WhitelabelSettings.objects.get(subdomain='ikonotv').user
        except WhitelabelSettings.DoesNotExist:
            ikonotv_admin = None

        super(IkonotvSubmittedPieceFilter, self).__init__(ikonotv_admin, *args, **kwargs)