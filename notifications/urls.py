from rest_framework import routers
from notifications.api import PieceNotificationEndpoint, EditionNotificationEndpoint, \
    ContractAgreementNotificationEndpoint

router = routers.DefaultRouter()
router.register(r'/pieces', PieceNotificationEndpoint)
router.register(r'/editions', EditionNotificationEndpoint)
router.register(r'/contract_agreements', ContractAgreementNotificationEndpoint)
urlpatterns = router.urls
