from django.conf.urls import patterns, include, url
from rest_framework import routers

from whitelabel import api as whitelabel_api

urlpatterns = patterns(
    '',
    url(r'^/cyland', include('whitelabel.cyland.urls', namespace='cyland')),
    url(r'^/ikonotv', include('whitelabel.ikonotv.urls', namespace='ikonotv')),
    url(r'^/', include('whitelabel.market.urls', namespace='market')),
)

router = routers.DefaultRouter()
router.register(r'/settings', whitelabel_api.WhitelabelSettingsEndpoint)

urlpatterns += router.urls
