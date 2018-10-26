from django.conf.urls import patterns, include, url
from rest_framework_nested import routers
from prize import api as prize_api


router = routers.SimpleRouter()
router.register(r'prizes', prize_api.PrizeEndpoint)

domains_router = routers.NestedSimpleRouter(router, r'prizes', lookup='domain')
domains_router.register(r'ratings', prize_api.RatingEndpoint)
domains_router.register(r'notes', prize_api.PrizeNoteEndpoint)
domains_router.register(r'users', prize_api.PrizeUserEndpoint, base_name='prize-users')
domains_router.register(r'pieces', prize_api.PrizePieceEndpoint, base_name='prize-pieces')
domains_router.register(r'jury', prize_api.PrizeJuryEndpoint, base_name='prize-jury')

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^', include(domains_router.urls)),
)
