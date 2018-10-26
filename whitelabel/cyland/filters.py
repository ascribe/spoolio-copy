
from whitelabel.filters import SubmittedPieceFilter
from whitelabel.models import WhitelabelSettings


class CylandSubmittedPieceFilter(SubmittedPieceFilter):

    def __init__(self, *args, **kwargs):
        try:
            cyland_admin = WhitelabelSettings.objects.get(subdomain='cyland').user
        except WhitelabelSettings.DoesNotExist:
            cyland_admin = None

        super(CylandSubmittedPieceFilter, self).__init__(cyland_admin, *args, **kwargs)