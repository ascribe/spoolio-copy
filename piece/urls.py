from rest_framework import routers

from piece import api as piece_api

router = routers.DefaultRouter()
router.register(r'pieces', piece_api.PieceEndpoint )
router.register(r'editions', piece_api.EditionEndpoint )
urlpatterns = router.urls


