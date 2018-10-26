from django.conf.urls import patterns, include, url
from rest_framework_nested import routers

from whitelabel.market import api

router = routers.SimpleRouter()
router.register(r'markets', api.MarketEndpoint)
domains_router = routers.NestedSimpleRouter(router, r'markets', lookup='domain')

domains_router.register(r'users', api.MarketUserEndpoint)
domains_router.register(r'pieces', api.MarketPieceEndpoint)
domains_router.register(r'editions', api.MarketEditionEndpoint)

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^', include(domains_router.urls)),
)


